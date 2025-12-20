### UnexpectedModelBehavior

Bases: `AgentRunError`

Error caused by unexpected Model behavior, e.g. an unexpected response code.

Source code in `pydantic_ai_slim/pydantic_ai/exceptions.py`

```python
class UnexpectedModelBehavior(AgentRunError):
    """Error caused by unexpected Model behavior, e.g. an unexpected response code."""

    message: str
    """Description of the unexpected behavior."""
    body: str | None
    """The body of the response, if available."""

    def __init__(self, message: str, body: str | None = None):
        self.message = message
        if body is None:
            self.body: str | None = None
        else:
            try:
                self.body = json.dumps(json.loads(body), indent=2)
            except ValueError:
                self.body = body
        super().__init__(message)

    def __str__(self) -> str:
        if self.body:
            return f'{self.message}, body:\n{self.body}'
        else:
            return self.message

```

#### message

```python
message: str = message

```

Description of the unexpected behavior.

#### body

```python
body: str | None = dumps(loads(body), indent=2)

```

The body of the response, if available.
