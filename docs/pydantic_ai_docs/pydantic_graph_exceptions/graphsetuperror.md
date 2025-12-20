### GraphSetupError

Bases: `TypeError`

Error caused by an incorrectly configured graph.

Source code in `pydantic_graph/pydantic_graph/exceptions.py`

```python
class GraphSetupError(TypeError):
    """Error caused by an incorrectly configured graph."""

    message: str
    """Description of the mistake."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)

```

#### message

```python
message: str = message

```

Description of the mistake.
