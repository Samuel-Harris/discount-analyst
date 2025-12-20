## Caching and Idempotency

Prefect 3.0 provides built-in caching and transactional semantics. Tasks with identical inputs will not re-execute if their results are already cached, making workflows naturally idempotent and resilient to failures.

- **Task inputs**: Messages, settings, parameters, tool arguments, and serializable dependencies

**Note**: For user dependencies to be included in cache keys, they must be serializable (e.g., Pydantic models or basic Python types). Non-serializable dependencies are automatically excluded from cache computation.
