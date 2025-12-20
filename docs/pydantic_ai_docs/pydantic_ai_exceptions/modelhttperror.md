### ModelHTTPError

Bases: `ModelAPIError`

Raised when an model provider response has a status code of 4xx or 5xx.

Source code in `pydantic_ai_slim/pydantic_ai/exceptions.py`

```python
class ModelHTTPError(ModelAPIError):
    """Raised when an model provider response has a status code of 4xx or 5xx."""

    status_code: int
    """The HTTP status code returned by the API."""

    body: object | None
    """The body of the response, if available."""

    def __init__(self, status_code: int, model_name: str, body: object | None = None):
        self.status_code = status_code
        self.body = body
        message = f'status_code: {status_code}, model_name: {model_name}, body: {body}'
        super().__init__(model_name=model_name, message=message)

```

#### status_code

```python
status_code: int = status_code

```

The HTTP status code returned by the API.

#### body

```python
body: object | None = body

```

The body of the response, if available.
