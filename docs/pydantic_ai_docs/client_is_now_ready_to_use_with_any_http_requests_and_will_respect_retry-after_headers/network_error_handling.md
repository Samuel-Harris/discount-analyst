### Network Error Handling

network_error_handling.py

```python
import httpx
from tenacity import retry_if_exception_type, stop_after_attempt, wait_exponential

from pydantic_ai.retries import AsyncTenacityTransport, RetryConfig


def create_network_resilient_client():
    """Create a client that handles network errors with retries."""
    transport = AsyncTenacityTransport(
        config=RetryConfig(
            retry=retry_if_exception_type((
                httpx.TimeoutException,
                httpx.ConnectError,
                httpx.ReadError
            )),
            wait=wait_exponential(multiplier=1, max=10),
            stop=stop_after_attempt(3),
            reraise=True
        )
    )
    return httpx.AsyncClient(transport=transport)
