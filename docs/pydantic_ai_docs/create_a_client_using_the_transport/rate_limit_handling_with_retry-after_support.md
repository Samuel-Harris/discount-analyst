### Rate Limit Handling with Retry-After Support

rate_limit_handling.py

```python
from httpx import AsyncClient, HTTPStatusError
from tenacity import retry_if_exception_type, stop_after_attempt, wait_exponential

from pydantic_ai.retries import AsyncTenacityTransport, RetryConfig, wait_retry_after


def create_rate_limit_client():
    """Create a client that respects Retry-After headers from rate limiting responses."""
    transport = AsyncTenacityTransport(
        config=RetryConfig(
            retry=retry_if_exception_type(HTTPStatusError),
            wait=wait_retry_after(
                fallback_strategy=wait_exponential(multiplier=1, max=60),
                max_wait=300  # Don't wait more than 5 minutes
            ),
            stop=stop_after_attempt(10),
            reraise=True
        ),
        validate_response=lambda r: r.raise_for_status()  # Raises HTTPStatusError for 4xx/5xx
    )
    return AsyncClient(transport=transport)
