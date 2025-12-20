### TaskSendParams

Bases: `TypedDict`

Internal parameters for task execution within the framework.

Note: This is not part of the A2A protocol - it's used internally for broker/worker communication.

Source code in `.venv/lib/python3.12/site-packages/fasta2a/schema.py`

```python
@pydantic.with_config({'alias_generator': to_camel})
class TaskSendParams(TypedDict):
    """Internal parameters for task execution within the framework.

    Note: This is not part of the A2A protocol - it's used internally
    for broker/worker communication.
    """

    id: str
    """The id of the task."""

    context_id: str
    """The context id for the task."""

    message: Message
    """The message to process."""

    history_length: NotRequired[int]
    """Number of recent messages to be retrieved."""

    metadata: NotRequired[dict[str, Any]]
    """Extension metadata."""

```

#### id

```python
id: str

```

The id of the task.

#### context_id

```python
context_id: str

```

The context id for the task.

#### message

```python
message: Message

```

The message to process.

#### history_length

```python
history_length: NotRequired[int]

```

Number of recent messages to be retrieved.

#### metadata

```python
metadata: NotRequired[dict[str, Any]]

```

Extension metadata.
