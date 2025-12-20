### GraphNodeStatusError

Bases: `GraphRuntimeError`

Error caused by trying to run a node that already has status `'running'`, `'success'`, or `'error'`.

Source code in `pydantic_graph/pydantic_graph/exceptions.py`

```python
class GraphNodeStatusError(GraphRuntimeError):
    """Error caused by trying to run a node that already has status `'running'`, `'success'`, or `'error'`."""

    def __init__(self, actual_status: 'SnapshotStatus'):
        self.actual_status = actual_status
        super().__init__(f"Incorrect snapshot status {actual_status!r}, must be 'created' or 'pending'.")

    @classmethod
    def check(cls, status: 'SnapshotStatus') -> None:
        """Check if the status is valid."""
        if status not in {'created', 'pending'}:
            raise cls(status)

```

#### check

```python
check(status: SnapshotStatus) -> None

```

Check if the status is valid.

Source code in `pydantic_graph/pydantic_graph/exceptions.py`

```python
@classmethod
def check(cls, status: 'SnapshotStatus') -> None:
    """Check if the status is valid."""
    if status not in {'created', 'pending'}:
        raise cls(status)

```
