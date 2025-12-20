### TaskArtifactUpdateEvent

Bases: `TypedDict`

Sent by server during message/stream requests.

Source code in `.venv/lib/python3.12/site-packages/fasta2a/schema.py`

```python
@pydantic.with_config({'alias_generator': to_camel})
class TaskArtifactUpdateEvent(TypedDict):
    """Sent by server during message/stream requests."""

    task_id: str
    """The id of the task."""

    context_id: str
    """The context the task is associated with."""

    kind: Literal['artifact-update']
    """Event type identification."""

    artifact: Artifact
    """The artifact that was updated."""

    append: NotRequired[bool]
    """Whether to append to existing artifact (true) or replace (false)."""

    last_chunk: NotRequired[bool]
    """Indicates this is the final chunk of the artifact."""

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
kind: Literal['artifact-update']

```

Event type identification.

#### artifact

```python
artifact: Artifact

```

The artifact that was updated.

#### append

```python
append: NotRequired[bool]

```

Whether to append to existing artifact (true) or replace (false).

#### last_chunk

```python
last_chunk: NotRequired[bool]

```

Indicates this is the final chunk of the artifact.

#### metadata

```python
metadata: NotRequired[dict[str, Any]]

```

Extension metadata.
