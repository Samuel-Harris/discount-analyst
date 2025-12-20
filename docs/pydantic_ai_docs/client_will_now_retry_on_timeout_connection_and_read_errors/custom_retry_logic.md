### Custom Retry Logic

custom_retry_logic.py

```python
import httpx
from tenacity import retry_if_exception, stop_after_attempt, wait_exponential

from pydantic_ai.retries import AsyncTenacityTransport, RetryConfig, wait_retry_after


def create_custom_retry_client():
    """Create a client with custom retry logic."""
    def custom_retry_condition(exception):
        """Custom logic to determine if we should retry."""
        if isinstance(exception, httpx.HTTPStatusError):
            # Retry on server errors but not client errors
            return 500 <= exception.response.status_code < 600
        return isinstance(exception, httpx.TimeoutException | httpx.ConnectError)

    transport = AsyncTenacityTransport(
        config=RetryConfig(
            retry=retry_if_exception(custom_retry_condition),
            # Use wait_retry_after for smart waiting on rate limits,
            # with custom exponential backoff as fallback
            wait=wait_retry_after(
                fallback_strategy=wait_exponential(multiplier=2, max=30),
                max_wait=120
            ),
            stop=stop_after_attempt(5),
            reraise=True
        ),
        validate_response=lambda r: r.raise_for_status()
    )
    return httpx.AsyncClient(transport=transport)

client = create_custom_retry_client()
