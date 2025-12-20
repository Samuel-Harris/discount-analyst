### ModelAPIError

Bases: `AgentRunError`

Raised when a model provider API request fails.

Source code in `pydantic_ai_slim/pydantic_ai/exceptions.py`

```python
class ModelAPIError(AgentRunError):
    """Raised when a model provider API request fails."""

    model_name: str
    """The name of the model associated with the error."""

    def __init__(self, model_name: str, message: str):
        self.model_name = model_name
        super().__init__(message)

```

#### model_name

```python
model_name: str = model_name

```

The name of the model associated with the error.
