### AsyncTenacityTransport

For asynchronous HTTP clients (recommended for most use cases):

async_transport_example.py

```python
from httpx import AsyncClient
from tenacity import stop_after_attempt

from pydantic_ai.retries import AsyncTenacityTransport, RetryConfig


def validator(response):
    """Treat responses with HTTP status 4xx/5xx as failures that need to be retried.
    Without a response validator, only network errors and timeouts will result in a retry.
    """
    response.raise_for_status()
