### GraphRuntimeError

Bases: `RuntimeError`

Error caused by an issue during graph execution.

Source code in `pydantic_graph/pydantic_graph/exceptions.py`

```python
class GraphRuntimeError(RuntimeError):
    """Error caused by an issue during graph execution."""

    message: str
    """The error message."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)

```

#### message

```python
message: str = message

```

The error message.
