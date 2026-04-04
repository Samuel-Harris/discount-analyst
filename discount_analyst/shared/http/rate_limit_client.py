import asyncio
import re
from contextlib import AbstractAsyncContextManager
from copy import deepcopy
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


def _snapshot_messages_for_stream_retry[AgentDepsT = None, OutputT = str](
    result: StreamedRunResult[AgentDepsT, OutputT],
) -> list[ModelMessage]:
    """Return a deep-copied snapshot of completed messages for the next ``run_stream`` attempt.

    Chat completion APIs cannot reliably continue from a half-streamed assistant message, and
    pydantic-ai only adds the final assistant ``ModelResponse`` to history after the stream
    completes—so we never merge ``result.response`` or other partial tail content into history.
    """
    return [deepcopy(m) for m in result.all_messages()]


class _StreamedRunFacade[AgentDepsT = None, OutputT = str]:
    """Delegates to the active ``StreamedRunResult`` while ``stream_output`` may swap it on retry."""

    def __init__(
        self, retries_context: "StreamWithRetriesContext[AgentDepsT, OutputT]"
    ) -> None:
        self._retries_context = retries_context

    async def stream_output(
        self, *, debounce_by: float | None = 0.1
    ) -> AsyncIterator[OutputT]:
        while True:
            active = self._retries_context.active_streamed_result
            try:
                async for chunk in active.stream_output(debounce_by=debounce_by):
                    yield chunk
                return
            except BaseException as e:
                await self._retries_context.reopen_after_stream_interrupt(e)

    async def get_output(self) -> OutputT:
        return await self._retries_context.active_streamed_result.get_output()

    def usage(self) -> RunUsage:
        return self._retries_context.active_streamed_result.usage()

    def all_messages(self, **kwargs: Any) -> list[ModelMessage]:
        return self._retries_context.active_streamed_result.all_messages(**kwargs)


class StreamWithRetriesContext[AgentDepsT = None, OutputT = str](
    AbstractAsyncContextManager[_StreamedRunFacade[AgentDepsT, OutputT]],
):
    """Async context manager for resilient streaming (see ``stream_with_retries``)."""

    def __init__(
        self,
        *,
        agent: AbstractAgent[AgentDepsT, OutputT],
        user_prompt: str,
        usage_limits: UsageLimits,
    ) -> None:
        self._agent = agent
        self._user_prompt = user_prompt
        self._usage_limits = usage_limits
        self._next_message_history: list[ModelMessage] | None = None
        self._next_usage: RunUsage | None = None
        # Async CM from ``AbstractAgent.run_stream`` (owns graph teardown via ``__aexit__``).
        self._run_stream_context_manager: (
            AbstractAsyncContextManager[StreamedRunResult[AgentDepsT, OutputT]] | None
        ) = None
        self._result: StreamedRunResult[AgentDepsT, OutputT] | None = None
        self._attempt_index: int = 0

    @property
    def active_streamed_result(self) -> StreamedRunResult[AgentDepsT, OutputT]:
        if self._result is None:
            raise RuntimeError("stream_with_retries: no active streamed result")
        return self._result

    def _build_run_stream_context_manager(
        self,
    ) -> AbstractAsyncContextManager[StreamedRunResult[AgentDepsT, OutputT]]:
        # ``run_stream`` uses ``deps: AgentDepsT = None``; pyright rejects implicit ``None`` when
        # ``AgentDepsT`` is not provably optional. Pass a typed ``None`` explicitly.
        deps_none = cast(AgentDepsT, None)
        if self._next_message_history is None:
            return self._agent.run_stream(
                user_prompt=self._user_prompt,
                deps=deps_none,
                usage_limits=self._usage_limits,
            )
        return self._agent.run_stream(
            user_prompt=None,
            message_history=self._next_message_history,
            deps=deps_none,
            usage_limits=self._usage_limits,
            usage=self._next_usage,
        )

    async def _enter_stream_with_retries(self, *, start_attempt: int) -> None:
        if start_attempt >= MAX_STREAM_RETRY_ATTEMPTS:
            raise RuntimeError(
                "stream_with_retries: exhausted attempts before entering"
            )
        for attempt in range(start_attempt, MAX_STREAM_RETRY_ATTEMPTS):
            self._attempt_index = attempt
            run_stream_context_manager = self._build_run_stream_context_manager()
            try:
                result = await run_stream_context_manager.__aenter__()
            except BaseException as e:
                if (
                    not should_retry_streaming_error(e)
                    or attempt >= MAX_STREAM_RETRY_ATTEMPTS - 1
                ):
                    raise
                wait = streaming_retry_sleep_seconds(e, attempt)
                logfire.info(
                    "Agent stream start failed, retrying",
                    attempt=attempt + 1,
                    max_attempts=MAX_STREAM_RETRY_ATTEMPTS,
                    wait_s=wait,
                    error=str(e),
                )
                await asyncio.sleep(wait)
                continue
            self._run_stream_context_manager = run_stream_context_manager
            self._result = result
            return
        raise RuntimeError(
            "stream_with_retries: exhausted attempts without entering"
        )  # pragma: no cover

    async def __aenter__(self) -> _StreamedRunFacade[AgentDepsT, OutputT]:
        self._next_message_history = None
        self._next_usage = None
        await self._enter_stream_with_retries(start_attempt=0)
        return _StreamedRunFacade(self)

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: Any,
    ) -> bool | None:
        if self._run_stream_context_manager is None:
            return None
        return await self._run_stream_context_manager.__aexit__(
            exc_type, exc, traceback
        )

    async def reopen_after_stream_interrupt(self, e: BaseException) -> None:
        if self._result is None or self._run_stream_context_manager is None:
            raise AssertionError("stream interrupt with no active run") from e
        if (
            not should_retry_streaming_error(e)
            or self._attempt_index >= MAX_STREAM_RETRY_ATTEMPTS - 1
        ):
            await self._run_stream_context_manager.__aexit__(
                type(e), e, e.__traceback__
            )
            raise
        self._next_message_history = _snapshot_messages_for_stream_retry(self._result)
        self._next_usage = deepcopy(self._result.usage())
        await self._run_stream_context_manager.__aexit__(type(e), e, e.__traceback__)
        wait = streaming_retry_sleep_seconds(e, self._attempt_index)
        logfire.info(
            "Agent stream interrupted, retrying",
            attempt=self._attempt_index + 1,
            max_attempts=MAX_STREAM_RETRY_ATTEMPTS,
            wait_s=wait,
            error=str(e),
        )
        await asyncio.sleep(wait)
        await self._enter_stream_with_retries(start_attempt=self._attempt_index + 1)
        return


def stream_with_retries[AgentDepsT = None, OutputT = str](
    *,
    agent: AbstractAgent[AgentDepsT, OutputT],
    user_prompt: str,
    usage_limits: UsageLimits,
) -> StreamWithRetriesContext[AgentDepsT, OutputT]:
    """Stream agent output with retries on transient API errors.

    Tenacity's @retry does not work with async generators: exceptions occur during
    iteration (e.g. ``stream_output()``), not only when entering ``run_stream``.
    We use a manual retry loop around the full stream lifecycle.

    ``async with stream_with_retries(...) as result`` binds ``result`` to a thin façade whose
    ``stream_output()`` may restart ``run_stream`` on retryable errors. After a failure while
    streaming, the next attempt uses ``run_stream(user_prompt=None, message_history=..., usage=...)``
    with a deep-copied snapshot of ``all_messages()`` and ``deepcopy(usage())``. That preserves
    completed turns (e.g. tool rounds) and cumulative usage without duplicating the user message.
    We do **not** inject partial assistant text from ``result.response``—OpenAI-style chat APIs do
    not support resuming an incomplete assistant message as a prefill.

    Retrying assumes everything needed for the next model step is represented in that message
    history plus the same agent configuration. Mutable ``deps`` / run state, non-idempotent
    tools, or other hidden per-attempt state are **not** reset; design tools and deps to be
    idempotent or consistent if the model may see the same transcript again after a retry.
    """
    return StreamWithRetriesContext(
        agent=agent,
        user_prompt=user_prompt,
        usage_limits=usage_limits,
    )
