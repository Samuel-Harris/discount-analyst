### wait_retry_after

```python
wait_retry_after(
    fallback_strategy: (
        Callable[[RetryCallState], float] | None
    ) = None,
    max_wait: float = 300,
) -> Callable[[RetryCallState], float]

```

Create a tenacity-compatible wait strategy that respects HTTP Retry-After headers.

This wait strategy checks if the exception contains an HTTPStatusError with a Retry-After header, and if so, waits for the time specified in the header. If no header is present or parsing fails, it falls back to the provided strategy.

The Retry-After header can be in two formats:

- An integer representing seconds to wait
- An HTTP date string representing when to retry

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `fallback_strategy` | `Callable[[RetryCallState], float] | None` | Wait strategy to use when no Retry-After header is present or parsing fails. Defaults to exponential backoff with max 60s. | `None` | | `max_wait` | `float` | Maximum time to wait in seconds, regardless of header value. Defaults to 300 (5 minutes). | `300` |

Returns:

| Type | Description | | --- | --- | | `Callable[[RetryCallState], float]` | A wait function that can be used with tenacity retry decorators. |

Example

```python
from httpx import AsyncClient, HTTPStatusError
from tenacity import retry_if_exception_type, stop_after_attempt

from pydantic_ai.retries import AsyncTenacityTransport, RetryConfig, wait_retry_after

transport = AsyncTenacityTransport(
    RetryConfig(
        retry=retry_if_exception_type(HTTPStatusError),
        wait=wait_retry_after(max_wait=120),
        stop=stop_after_attempt(5),
        reraise=True
    ),
    validate_response=lambda r: r.raise_for_status()
)
client = AsyncClient(transport=transport)

```

Source code in `pydantic_ai_slim/pydantic_ai/retries.py`

````python
def wait_retry_after(
    fallback_strategy: Callable[[RetryCallState], float] | None = None, max_wait: float = 300
) -> Callable[[RetryCallState], float]:
    """Create a tenacity-compatible wait strategy that respects HTTP Retry-After headers.

    This wait strategy checks if the exception contains an HTTPStatusError with a
    Retry-After header, and if so, waits for the time specified in the header.
    If no header is present or parsing fails, it falls back to the provided strategy.

    The Retry-After header can be in two formats:
    - An integer representing seconds to wait
    - An HTTP date string representing when to retry

    Args:
        fallback_strategy: Wait strategy to use when no Retry-After header is present
                          or parsing fails. Defaults to exponential backoff with max 60s.
        max_wait: Maximum time to wait in seconds, regardless of header value.
                 Defaults to 300 (5 minutes).

    Returns:
        A wait function that can be used with tenacity retry decorators.

    Example:
        ```python
        from httpx import AsyncClient, HTTPStatusError
        from tenacity import retry_if_exception_type, stop_after_attempt

        from pydantic_ai.retries import AsyncTenacityTransport, RetryConfig, wait_retry_after

        transport = AsyncTenacityTransport(
            RetryConfig(
                retry=retry_if_exception_type(HTTPStatusError),
                wait=wait_retry_after(max_wait=120),
                stop=stop_after_attempt(5),
                reraise=True
            ),
            validate_response=lambda r: r.raise_for_status()
        )
        client = AsyncClient(transport=transport)
        ```
    """
    if fallback_strategy is None:
        fallback_strategy = wait_exponential(multiplier=1, max=60)

    def wait_func(state: RetryCallState) -> float:
        exc = state.outcome.exception() if state.outcome else None
        if isinstance(exc, HTTPStatusError):
            retry_after = exc.response.headers.get('retry-after')
            if retry_after:
                try:
                    # Try parsing as seconds first
                    wait_seconds = int(retry_after)
                    return min(float(wait_seconds), max_wait)
                except ValueError:
                    # Try parsing as HTTP date
                    try:
                        retry_time = cast(datetime, parsedate_to_datetime(retry_after))
                        assert isinstance(retry_time, datetime)
                        now = datetime.now(timezone.utc)
                        wait_seconds = (retry_time - now).total_seconds()

                        if wait_seconds > 0:
                            return min(wait_seconds, max_wait)
                    except (ValueError, TypeError, AssertionError):
                        # If date parsing fails, fall back to fallback strategy
                        pass

        # Use fallback strategy
        return fallback_strategy(state)

    return wait_func

````
