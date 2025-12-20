### GraphBuildingError

Bases: `ValueError`

An error raised during graph-building.

Source code in `pydantic_graph/pydantic_graph/exceptions.py`

```python
class GraphBuildingError(ValueError):
    """An error raised during graph-building."""

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
