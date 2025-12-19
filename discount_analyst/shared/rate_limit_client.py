from httpx import AsyncClient, HTTPStatusError
from tenacity import retry_if_exception_type, stop_after_attempt, wait_exponential

from pydantic_ai.retries import AsyncTenacityTransport, RetryConfig, wait_retry_after


def create_rate_limit_client() -> AsyncClient:
    transport = AsyncTenacityTransport(
        config=RetryConfig(
            retry=retry_if_exception_type(HTTPStatusError),
            wait=wait_retry_after(
                fallback_strategy=wait_exponential(multiplier=10, max=90),
                max_wait=120,  # Don't wait more than 2 minutes
            ),
            stop=stop_after_attempt(6),
            reraise=True,
        ),
        validate_response=lambda r: r.raise_for_status(),
    )
    return AsyncClient(transport=transport)
