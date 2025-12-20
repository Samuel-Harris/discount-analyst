### check_allow_model_requests

```python
check_allow_model_requests() -> None

```

Check if model requests are allowed.

If you're defining your own models that have costs or latency associated with their use, you should call this in Model.request and Model.request_stream.

Raises:

| Type | Description | | --- | --- | | `RuntimeError` | If model requests are not allowed. |

Source code in `pydantic_ai_slim/pydantic_ai/models/__init__.py`

```python
def check_allow_model_requests() -> None:
    """Check if model requests are allowed.

    If you're defining your own models that have costs or latency associated with their use, you should call this in
    [`Model.request`][pydantic_ai.models.Model.request] and [`Model.request_stream`][pydantic_ai.models.Model.request_stream].

    Raises:
        RuntimeError: If model requests are not allowed.
    """
    if not ALLOW_MODEL_REQUESTS:
        raise RuntimeError('Model requests are not allowed, since ALLOW_MODEL_REQUESTS is False')

```
