from httpx import AsyncClient, HTTPStatusError, TimeoutException
from openai import APITimeoutError, InternalServerError, RateLimitError
from tenacity import retry_if_exception_type, stop_after_attempt, wait_exponential

from pydantic_ai.retries import AsyncTenacityTransport, RetryConfig, wait_retry_after

# Retry on rate limits (429), timeouts, and resource unavailable (503)
_RETRY_EXCEPTIONS = (
    HTTPStatusError,
    TimeoutException,
    APITimeoutError,
    RateLimitError,
    InternalServerError,
)


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
                fallback_strategy=wait_exponential(multiplier=10, max=90),
                max_wait=120,  # Don't wait more than 2 minutes
            ),
            stop=stop_after_attempt(6),
            reraise=True,
        ),
        validate_response=lambda r: r.raise_for_status(),
    )
    return AsyncClient(transport=transport, timeout=timeout)
