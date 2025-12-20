Retries utilities based on tenacity, especially for HTTP requests.

This module provides HTTP transport wrappers and wait strategies that integrate with the tenacity library to add retry capabilities to HTTP requests. The transports can be used with HTTP clients that support custom transports (such as httpx), while the wait strategies can be used with any tenacity retry decorator.

The module includes:

- TenacityTransport: Synchronous HTTP transport with retry capabilities
- AsyncTenacityTransport: Asynchronous HTTP transport with retry capabilities
- wait_retry_after: Wait strategy that respects HTTP Retry-After headers
