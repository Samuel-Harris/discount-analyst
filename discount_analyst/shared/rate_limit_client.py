import asyncio
import sys
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator
from httpx import (
    AsyncClient,
    ConnectError,
    HTTPStatusError,
    ReadTimeout,
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
from tenacity import retry_if_exception_type, stop_after_attempt, wait_exponential

from pydantic_ai.retries import AsyncTenacityTransport, RetryConfig, wait_retry_after

# Retry on rate limits (429), timeouts (incl. ReadTimeout for long Gemini runs), connection failures, and resource unavailable (503)
_RETRY_EXCEPTIONS = (
    HTTPStatusError,
    TimeoutException,
    ReadTimeout,
    ConnectError,
    APITimeoutError,
    APIConnectionError,
    RateLimitError,
    InternalServerError,
    APIError,
)

_STREAMING_RETRY_EXCEPTIONS = (APIError,)

RETRY_WAIT_MULTIPLIER = 10
RETRY_AFTER_MAX_WEIGHT_SECONDS = 120  # Max wait after receiving a Retry-After header
FALLBACK_MAX_WEIGHT_SECONDS = 90  # Max wait on fallback after error
MAX_RETRY_ATTEMPTS = 3


def create_rate_limit_client(*, timeout: float | None = None) -> AsyncClient:
    """Create an async HTTP client with retries for rate limits and timeouts.

    Args:
        timeout: Request timeout in seconds. None uses httpx default (5s).
            Use 1200 for 20 minutes for long-running OpenAI requests.
    """
    transport = AsyncTenacityTransport(
        config=RetryConfig(
            retry=retry_if_exception_type(_RETRY_EXCEPTIONS),
            wait=wait_retry_after(
                fallback_strategy=wait_exponential(
                    multiplier=RETRY_WAIT_MULTIPLIER, max=FALLBACK_MAX_WEIGHT_SECONDS
                ),
                max_wait=RETRY_AFTER_MAX_WEIGHT_SECONDS,
            ),
            stop=stop_after_attempt(6),
            reraise=True,
        ),
        validate_response=lambda r: r.raise_for_status(),
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
