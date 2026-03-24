import asyncio
import sys
from contextlib import asynccontextmanager
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
from pydantic_ai.result import StreamedRunResult
from pydantic_ai.usage import UsageLimits
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


_STREAMING_RETRY_EXCEPTIONS = (APIError,)

RETRY_WAIT_MULTIPLIER = 10
RETRY_AFTER_MAX_WEIGHT_SECONDS = 120  # Max wait after receiving a Retry-After header
FALLBACK_MAX_WEIGHT_SECONDS = 90  # Max wait on fallback after error
MAX_RETRY_ATTEMPTS = 3

_OPENAI_API_HOST = "api.openai.com"
# Cap logged bodies so Logfire and local logs stay usable on huge error payloads.
_MAX_OPENAI_ERROR_BODY_CHARS = 16_000


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


@asynccontextmanager
async def stream_with_retries[T](
    *,
    agent: AbstractAgent[Any, T],
    user_prompt: str,
    usage_limits: UsageLimits | None = None,
) -> AsyncIterator[StreamedRunResult[Any, T]]:
    """Stream agent output with retries on transient API errors.

    Tenacity's @retry does not work with async generators: exceptions occur during
    iteration (when entering the context), not during the initial call. We use a
    manual retry loop around agent.run_stream() entry instead.
    """
    last_exception: BaseException | None = None
    for attempt in range(MAX_RETRY_ATTEMPTS):
        cm = agent.run_stream(user_prompt, usage_limits=usage_limits)
        try:
            result = await cm.__aenter__()
        except _STREAMING_RETRY_EXCEPTIONS as e:
            last_exception = e
            if attempt < MAX_RETRY_ATTEMPTS - 1:
                await asyncio.sleep(_stream_wait(attempt))
            else:
                raise
        else:
            try:
                yield result
            finally:
                exc_type, exc_val, exc_tb = sys.exc_info()
                if exc_type is GeneratorExit:
                    exc_type, exc_val, exc_tb = None, None, None
                await cm.__aexit__(exc_type, exc_val, exc_tb)
            return
    if last_exception is not None:
        raise last_exception
