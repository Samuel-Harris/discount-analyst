### AgentRunError

Bases: `RuntimeError`

Base class for errors occurring during an agent run.

Source code in `pydantic_ai_slim/pydantic_ai/exceptions.py`

```python
class AgentRunError(RuntimeError):
    """Base class for errors occurring during an agent run."""

    message: str
    """The error message."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)

    def __str__(self) -> str:
        return self.message

```

#### message

```python
message: str = message

```

The error message.
