### TaskStatusUpdateEvent

Bases: `TypedDict`

Sent by server during message/stream requests.

Source code in `.venv/lib/python3.12/site-packages/fasta2a/schema.py`

```python
@pydantic.with_config({'alias_generator': to_camel})
class TaskStatusUpdateEvent(TypedDict):
    """Sent by server during message/stream requests."""

    task_id: str
    """The id of the task."""

    context_id: str
    """The context the task is associated with."""

    kind: Literal['status-update']
    """Event type."""

    status: TaskStatus
    """The status of the task."""

    final: bool
    """Indicates the end of the event stream."""

    metadata: NotRequired[dict[str, Any]]
    """Extension metadata."""

```

#### task_id

```python
task_id: str

```

The id of the task.

#### context_id

```python
context_id: str

```

The context the task is associated with.

#### kind

```python
kind: Literal['status-update']

```

Event type.

#### status

```python
status: TaskStatus

```

The status of the task.

#### final

```python
final: bool

```

Indicates the end of the event stream.

#### metadata

```python
metadata: NotRequired[dict[str, Any]]

```

Extension metadata.
