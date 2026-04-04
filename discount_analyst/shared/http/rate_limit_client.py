import asyncio
from copy import deepcopy
import re
from contextlib import AbstractAsyncContextManager
from typing import Any, AsyncIterator, cast

import logfire
from httpx import (
    AsyncClient,
    ConnectError,
    HTTPStatusError,
    ReadTimeout,
    Request,
    Response,
    TimeoutException,
)
from openai import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    InternalServerError,
    RateLimitError,
)
from pydantic_ai.agent.abstract import AbstractAgent
from pydantic_ai.messages import ModelMessage
from pydantic_ai.result import StreamedRunResult
from pydantic_ai.usage import RunUsage, UsageLimits
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from pydantic_ai.retries import AsyncTenacityTransport, RetryConfig, wait_retry_after


def _http_transport_should_retry(exc: BaseException) -> bool:
    """Retry only transient failures — not 4xx validation/auth (except 408/429)."""
    if isinstance(exc, HTTPStatusError):
        status = exc.response.status_code
        if status in (408, 429) or status >= 500:
            return True
        return False
    return isinstance(
        exc,
        (
            TimeoutException,
            ReadTimeout,
            ConnectError,
            APITimeoutError,
            APIConnectionError,
            RateLimitError,
            InternalServerError,
        ),
    )


_STREAMING_RETRY_HINT_TRY_AGAIN = re.compile(
    r"try\s+again\s+in\s+(\d+\.?\d*)\s*s", re.IGNORECASE
)

RETRY_WAIT_MULTIPLIER = 10
RETRY_AFTER_MAX_WEIGHT_SECONDS = 120  # Max wait after receiving a Retry-After header
FALLBACK_MAX_WEIGHT_SECONDS = 90  # Max wait on fallback after error
# Streaming can fail mid-`stream_output()` (e.g. OpenAI TPM) after a successful `run_stream` start.
MAX_STREAM_RETRY_ATTEMPTS = 6

_OPENAI_API_HOST = "api.openai.com"
# Cap logged bodies so Logfire and local logs stay usable on huge error payloads.
_MAX_OPENAI_ERROR_BODY_CHARS = 16_000


def _openai_error_text(exc: BaseException) -> str:
    if isinstance(exc, APIError):
        msg = getattr(exc, "message", None)
        if msg:
            return str(msg)
    return str(exc)


def api_error_indicates_rate_limit(exc: APIError) -> bool:
    """True when OpenAI signals quota / TPM / RPM limits (not all APIError cases)."""
    text = _openai_error_text(exc).lower()
    return any(
        needle in text
        for needle in (
            "rate limit",
            "tokens per min",
            "requests per min",
            "tpm",
            "rpm",
            "too many requests",
        )
    )


def should_retry_streaming_error(exc: BaseException) -> bool:
    """Whether to backoff and restart a streamed agent run."""
    if isinstance(
        exc, (RateLimitError, InternalServerError, APITimeoutError, APIConnectionError)
    ):
        return True
    if isinstance(exc, APIError):
        return api_error_indicates_rate_limit(exc)
    return False


def _log_openai_http_error_if_applicable(response: Response) -> None:
    """Emit Logfire details when OpenAI returns a non-success HTTP status.

    OpenAI often puts the actionable reason in the JSON body; the generic
    ``HTTPStatusError`` / ``APIConnectionError`` chain does not surface it clearly.
    """
    if not response.is_error:
        return
    # These statuses are retried by the transport; logging each attempt floods Logfire.
    if response.status_code in (408, 429):
        return
    url = str(response.request.url)
    if _OPENAI_API_HOST not in url:
        return
    try:
        body = response.text
    except Exception:
        try:
            raw = response.content
            body = raw.decode(response.encoding or "utf-8", errors="replace")
        except Exception:
            body = "<response body unavailable>"
    if len(body) > _MAX_OPENAI_ERROR_BODY_CHARS:
        body = f"{body[:_MAX_OPENAI_ERROR_BODY_CHARS]}…(truncated)"
    logfire.warning(
        "OpenAI HTTP error response",
        status_code=response.status_code,
        method=response.request.method,
        url=url,
        response_body=body,
    )


def _validate_http_response(response: Response) -> None:
    _log_openai_http_error_if_applicable(response)
    response.raise_for_status()


class _AsyncTenacityTransportWithErrorBody(AsyncTenacityTransport):
    """Like ``AsyncTenacityTransport`` but buffers error bodies before validation.

    httpx async ``Response.text`` raises ``ResponseNotRead`` until
    ``await response.aread()`` runs. The upstream transport calls the sync
    ``validate_response`` hook immediately, so without this step OpenAI JSON
    errors never reach ``response.text`` and Logfire logged
    ``<response body unavailable>``.

    Only ``response.is_error`` responses are read here so successful streaming
    bodies are not fully buffered before the SDK consumes them.
    """

    async def handle_async_request(self, request: Request) -> Response:
        @retry(**cast(dict[str, Any], self.config))
        async def handle_async_request_inner(req: Request) -> Response:
            response = await self.wrapped.handle_async_request(req)
            response.request = req
            if response.is_error:
                try:
                    await response.aread()
                except Exception as e:
                    logfire.warning(
                        "OpenAI error response aread failed",
                        error_type=type(e).__name__,
                        url=str(req.url),
                        status_code=response.status_code,
                    )
            if self.validate_response:
                try:
                    self.validate_response(response)
                except Exception:
                    await response.aclose()
                    raise
            return response

        return await handle_async_request_inner(request)


def create_rate_limit_client(*, timeout: float | None = None) -> AsyncClient:
    """Create an async HTTP client with retries for rate limits and timeouts.

    Args:
        timeout: Request timeout in seconds. None uses httpx default (5s).
            Use 1200 for 20 minutes for long-running OpenAI requests.
    """
    transport = _AsyncTenacityTransportWithErrorBody(
        config=RetryConfig(
            retry=retry_if_exception(_http_transport_should_retry),
            wait=wait_retry_after(
                fallback_strategy=wait_exponential(
                    multiplier=RETRY_WAIT_MULTIPLIER, max=FALLBACK_MAX_WEIGHT_SECONDS
                ),
                max_wait=RETRY_AFTER_MAX_WEIGHT_SECONDS,
            ),
            stop=stop_after_attempt(6),
            reraise=True,
        ),
        validate_response=_validate_http_response,
    )
    return AsyncClient(transport=transport, timeout=timeout)


def _stream_wait(attempt: int) -> float:
    """Wait time for streaming retries (exponential backoff, capped)."""
    return min(
        RETRY_WAIT_MULTIPLIER * (2**attempt),
        FALLBACK_MAX_WEIGHT_SECONDS,
    )


def streaming_retry_sleep_seconds(exc: BaseException, attempt: int) -> float:
    """Sleep before retry; prefer OpenAI's suggested delay when present."""
    text = _openai_error_text(exc)
    m = _STREAMING_RETRY_HINT_TRY_AGAIN.search(text)
    if m:
        suggested = float(m.group(1))
        # Small cushion so the TPM window has cleared.
        return min(max(suggested + 1.0, 1.0), RETRY_AFTER_MAX_WEIGHT_SECONDS)
    return min(_stream_wait(attempt), FALLBACK_MAX_WEIGHT_SECONDS)


class StreamWithRetriesContext[T]:
    """Own stream attempts and reopen safely on retryable interruptions."""

    def __init__(
        self,
        *,
        agent: AbstractAgent[Any, T],
        user_prompt: str,
        usage_limits: UsageLimits,
    ) -> None:
        self._agent = agent
        self._user_prompt = user_prompt
        self._usage_limits = usage_limits

        self._next_message_history: list[ModelMessage] | None = None
        self._next_usage: RunUsage | None = None

        self._run_stream_context_manager: (
            AbstractAsyncContextManager[StreamedRunResult[Any, T]] | None
        ) = None
        self._active_streamed_result: StreamedRunResult[Any, T] | None = None
        self._attempt_index = 0

        self._result = StreamedResultWrapper(self)

    async def __aenter__(self) -> "StreamedResultWrapper[T]":
        await self._open_attempt_with_retries()
        return self._result

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: Any,
    ) -> None:
        await self._close_active_attempt(exc_type, exc, traceback)

    @property
    def active_streamed_result(self) -> StreamedRunResult[Any, T]:
        if self._active_streamed_result is None:
            raise RuntimeError("No active stream attempt is open.")
        return self._active_streamed_result

    async def reopen_after_stream_interrupt(self, exc: BaseException) -> None:
        """Handle a stream error, optionally reopening a fresh attempt."""
        if not should_retry_streaming_error(exc) or self._attempt_index >= (
            MAX_STREAM_RETRY_ATTEMPTS - 1
        ):
            await self._close_active_attempt(type(exc), exc, exc.__traceback__)
            raise exc

        self._next_message_history = deepcopy(
            self.active_streamed_result.all_messages()
        )
        self._next_usage = deepcopy(self.active_streamed_result.usage())

        await self._close_active_attempt(type(exc), exc, exc.__traceback__)
        wait = streaming_retry_sleep_seconds(exc, self._attempt_index)
        logfire.info(
            "Agent stream interrupted, retrying",
            attempt=self._attempt_index + 1,
            max_attempts=MAX_STREAM_RETRY_ATTEMPTS,
            wait_s=wait,
            error=str(exc),
        )
        await asyncio.sleep(wait)
        self._attempt_index += 1
        await self._open_attempt_with_retries()

    async def _open_attempt_with_retries(self) -> None:
        while True:
            context_manager = self._agent.run_stream(
                self._next_user_prompt(),
                message_history=self._next_message_history,
                usage_limits=self._usage_limits,
                usage=self._next_usage,
            )
            try:
                result = await context_manager.__aenter__()
            except BaseException as exc:
                if not should_retry_streaming_error(exc) or self._attempt_index >= (
                    MAX_STREAM_RETRY_ATTEMPTS - 1
                ):
                    raise
                wait = streaming_retry_sleep_seconds(exc, self._attempt_index)
                logfire.info(
                    "Agent stream start failed, retrying",
                    attempt=self._attempt_index + 1,
                    max_attempts=MAX_STREAM_RETRY_ATTEMPTS,
                    wait_s=wait,
                    error=str(exc),
                )
                await asyncio.sleep(wait)
                self._attempt_index += 1
                continue

            self._run_stream_context_manager = context_manager
            self._active_streamed_result = result
            return

    def _next_user_prompt(self) -> str | None:
        if self._next_message_history is None:
            return self._user_prompt
        return None

    async def _close_active_attempt(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: Any,
    ) -> None:
        context_manager = self._run_stream_context_manager
        if context_manager is None:
            return
        try:
            await context_manager.__aexit__(exc_type, exc, traceback)
        finally:
            self._run_stream_context_manager = None
            self._active_streamed_result = None


class StreamedResultWrapper[T]:
    """Retry-aware facade that delegates to the active streamed result."""

    def __init__(self, retries_context: StreamWithRetriesContext[T]) -> None:
        self._retries_context = retries_context

    @property
    def _active_result(self) -> StreamedRunResult[Any, T]:
        return self._retries_context.active_streamed_result

    async def stream_output(
        self, *, debounce_by: float | None = 0.1
    ) -> AsyncIterator[T]:
        for _ in range(MAX_STREAM_RETRY_ATTEMPTS):
            try:
                async for output in self._active_result.stream_output(
                    debounce_by=debounce_by
                ):
                    yield output
            except BaseException as exc:
                await self._retries_context.reopen_after_stream_interrupt(exc)
                continue
            return
        raise RuntimeError("Stream retries exhausted without terminal result")

    async def get_output(self) -> T:
        for _ in range(MAX_STREAM_RETRY_ATTEMPTS):
            try:
                return await self._active_result.get_output()
            except BaseException as exc:
                await self._retries_context.reopen_after_stream_interrupt(exc)
        raise RuntimeError("Output retries exhausted without terminal result")

    def usage(self) -> RunUsage:
        return self._active_result.usage()

    def all_messages(
        self, *, output_tool_return_content: str | None = None
    ) -> list[ModelMessage]:
        return self._active_result.all_messages(
            output_tool_return_content=output_tool_return_content
        )


def stream_with_retries[T](
    *,
    agent: AbstractAgent[Any, T],
    user_prompt: str,
    usage_limits: UsageLimits,
) -> StreamWithRetriesContext[T]:
    """Stream agent output with retries on transient API errors.

    Tenacity's @retry does not work with async generators: exceptions can occur
    during stream iteration (e.g. ``stream_output()``), not only entering
    ``run_stream``. This context manager keeps attempt lifecycle state so
    retryable interruptions can reopen safely with resumed message history/usage.
    """
    return StreamWithRetriesContext(
        agent=agent,
        user_prompt=user_prompt,
        usage_limits=usage_limits,
    )
