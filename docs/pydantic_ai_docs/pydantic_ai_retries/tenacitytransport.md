### TenacityTransport

Bases: `BaseTransport`

Synchronous HTTP transport with tenacity-based retry functionality.

This transport wraps another BaseTransport and adds retry capabilities using the tenacity library. It can be configured to retry requests based on various conditions such as specific exception types, response status codes, or custom validation logic.

The transport works by intercepting HTTP requests and responses, allowing the tenacity controller to determine when and how to retry failed requests. The validate_response function can be used to convert HTTP responses into exceptions that trigger retries.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `wrapped` | `BaseTransport | None` | The underlying transport to wrap and add retry functionality to. | `None` | | `config` | `RetryConfig` | The arguments to use for the tenacity retry decorator, including retry conditions, wait strategy, stop conditions, etc. See the tenacity docs for more info. | _required_ | | `validate_response` | `Callable[[Response], Any] | None` | Optional callable that takes a Response and can raise an exception to be handled by the controller if the response should trigger a retry. Common use case is to raise exceptions for certain HTTP status codes. If None, no response validation is performed. | `None` |

Example

```python
from httpx import Client, HTTPStatusError, HTTPTransport
from tenacity import retry_if_exception_type, stop_after_attempt

from pydantic_ai.retries import RetryConfig, TenacityTransport, wait_retry_after

transport = TenacityTransport(
    RetryConfig(
        retry=retry_if_exception_type(HTTPStatusError),
        wait=wait_retry_after(max_wait=300),
        stop=stop_after_attempt(5),
        reraise=True
    ),
    HTTPTransport(),
    validate_response=lambda r: r.raise_for_status()
)
client = Client(transport=transport)

```

Source code in `pydantic_ai_slim/pydantic_ai/retries.py`

````python
class TenacityTransport(BaseTransport):
    """Synchronous HTTP transport with tenacity-based retry functionality.

    This transport wraps another BaseTransport and adds retry capabilities using the tenacity library.
    It can be configured to retry requests based on various conditions such as specific exception types,
    response status codes, or custom validation logic.

    The transport works by intercepting HTTP requests and responses, allowing the tenacity controller
    to determine when and how to retry failed requests. The validate_response function can be used
    to convert HTTP responses into exceptions that trigger retries.

    Args:
        wrapped: The underlying transport to wrap and add retry functionality to.
        config: The arguments to use for the tenacity `retry` decorator, including retry conditions,
            wait strategy, stop conditions, etc. See the tenacity docs for more info.
        validate_response: Optional callable that takes a Response and can raise an exception
            to be handled by the controller if the response should trigger a retry.
            Common use case is to raise exceptions for certain HTTP status codes.
            If None, no response validation is performed.

    Example:
        ```python
        from httpx import Client, HTTPStatusError, HTTPTransport
        from tenacity import retry_if_exception_type, stop_after_attempt

        from pydantic_ai.retries import RetryConfig, TenacityTransport, wait_retry_after

        transport = TenacityTransport(
            RetryConfig(
                retry=retry_if_exception_type(HTTPStatusError),
                wait=wait_retry_after(max_wait=300),
                stop=stop_after_attempt(5),
                reraise=True
            ),
            HTTPTransport(),
            validate_response=lambda r: r.raise_for_status()
        )
        client = Client(transport=transport)
        ```
    """

    def __init__(
        self,
        config: RetryConfig,
        wrapped: BaseTransport | None = None,
        validate_response: Callable[[Response], Any] | None = None,
    ):
        self.config = config
        self.wrapped = wrapped or HTTPTransport()
        self.validate_response = validate_response

    def handle_request(self, request: Request) -> Response:
        """Handle an HTTP request with retry logic.

        Args:
            request: The HTTP request to handle.

        Returns:
            The HTTP response.

        Raises:
            RuntimeError: If the retry controller did not make any attempts.
            Exception: Any exception raised by the wrapped transport or validation function.
        """

        @retry(**self.config)
        def handle_request(req: Request) -> Response:
            response = self.wrapped.handle_request(req)

            # this is normally set by httpx _after_ calling this function, but we want the request in the validator:
            response.request = req

            if self.validate_response:
                try:
                    self.validate_response(response)
                except Exception:
                    response.close()
                    raise
            return response

        return handle_request(request)

    def __enter__(self) -> TenacityTransport:
        self.wrapped.__enter__()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_value: BaseException | None = None,
        traceback: TracebackType | None = None,
    ) -> None:
        self.wrapped.__exit__(exc_type, exc_value, traceback)

    def close(self) -> None:
        self.wrapped.close()  # pragma: no cover

````

#### handle_request

```python
handle_request(request: Request) -> Response

```

Handle an HTTP request with retry logic.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `request` | `Request` | The HTTP request to handle. | _required_ |

Returns:

| Type | Description | | --- | --- | | `Response` | The HTTP response. |

Raises:

| Type | Description | | --- | --- | | `RuntimeError` | If the retry controller did not make any attempts. | | `Exception` | Any exception raised by the wrapped transport or validation function. |

Source code in `pydantic_ai_slim/pydantic_ai/retries.py`

```python
def handle_request(self, request: Request) -> Response:
    """Handle an HTTP request with retry logic.

    Args:
        request: The HTTP request to handle.

    Returns:
        The HTTP response.

    Raises:
        RuntimeError: If the retry controller did not make any attempts.
        Exception: Any exception raised by the wrapped transport or validation function.
    """

    @retry(**self.config)
    def handle_request(req: Request) -> Response:
        response = self.wrapped.handle_request(req)

        # this is normally set by httpx _after_ calling this function, but we want the request in the validator:
        response.request = req

        if self.validate_response:
            try:
                self.validate_response(response)
            except Exception:
                response.close()
                raise
        return response

    return handle_request(request)

```
