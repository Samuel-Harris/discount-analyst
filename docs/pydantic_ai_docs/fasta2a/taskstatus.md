### TaskStatus

Bases: `TypedDict`

Status and accompanying message for a task.

Source code in `.venv/lib/python3.12/site-packages/fasta2a/schema.py`

```python
@pydantic.with_config({'alias_generator': to_camel})
class TaskStatus(TypedDict):
    """Status and accompanying message for a task."""

    state: TaskState
    """The current state of the task."""

    message: NotRequired[Message]
    """Additional status updates for client."""

    timestamp: NotRequired[str]
    """ISO datetime value of when the status was updated."""

```

#### state

```python
state: TaskState

```

The current state of the task.

#### message

```python
message: NotRequired[Message]

```

Additional status updates for client.

#### timestamp

```python
timestamp: NotRequired[str]

```

ISO datetime value of when the status was updated.
