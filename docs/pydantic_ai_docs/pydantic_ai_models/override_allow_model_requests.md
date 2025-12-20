### override_allow_model_requests

```python
override_allow_model_requests(
    allow_model_requests: bool,
) -> Iterator[None]

```

Context manager to temporarily override ALLOW_MODEL_REQUESTS.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `allow_model_requests` | `bool` | Whether to allow model requests within the context. | _required_ |

Source code in `pydantic_ai_slim/pydantic_ai/models/__init__.py`

```python
@contextmanager
def override_allow_model_requests(allow_model_requests: bool) -> Iterator[None]:
    """Context manager to temporarily override [`ALLOW_MODEL_REQUESTS`][pydantic_ai.models.ALLOW_MODEL_REQUESTS].

    Args:
        allow_model_requests: Whether to allow model requests within the context.
    """
    global ALLOW_MODEL_REQUESTS
    old_value = ALLOW_MODEL_REQUESTS
    ALLOW_MODEL_REQUESTS = allow_model_requests  # pyright: ignore[reportConstantRedefinition]
    try:
        yield
    finally:
        ALLOW_MODEL_REQUESTS = old_value  # pyright: ignore[reportConstantRedefinition]

```
