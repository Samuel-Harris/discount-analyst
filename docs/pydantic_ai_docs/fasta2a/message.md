### Message

Bases: `TypedDict`

A Message contains any content that is not an Artifact.

This can include things like agent thoughts, user context, instructions, errors, status, or metadata.

All content from a client comes in the form of a Message. Agents send Messages to communicate status or to provide instructions (whereas generated results are sent as Artifacts).

A Message can have multiple parts to denote different pieces of content. For example, a user request could include a textual description from a user and then multiple files used as context from the client.

Source code in `.venv/lib/python3.12/site-packages/fasta2a/schema.py`

```python
@pydantic.with_config({'alias_generator': to_camel})
class Message(TypedDict):
    """A Message contains any content that is not an Artifact.

    This can include things like agent thoughts, user context, instructions, errors, status, or metadata.

    All content from a client comes in the form of a Message. Agents send Messages to communicate status or to provide
    instructions (whereas generated results are sent as Artifacts).

    A Message can have multiple parts to denote different pieces of content. For example, a user request could include
    a textual description from a user and then multiple files used as context from the client.
    """

    role: Literal['user', 'agent']
    """The role of the message."""

    parts: list[Part]
    """The parts of the message."""

    kind: Literal['message']
    """Event type."""

    metadata: NotRequired[dict[str, Any]]
    """Metadata about the message."""

    # Additional fields
    message_id: str
    """Identifier created by the message creator."""

    context_id: NotRequired[str]
    """The context the message is associated with."""

    task_id: NotRequired[str]
    """Identifier of task the message is related to."""

    reference_task_ids: NotRequired[list[str]]
    """Array of task IDs this message references."""

    extensions: NotRequired[list[str]]
    """Array of extensions."""

```

#### role

```python
role: Literal['user', 'agent']

```

The role of the message.

#### parts

```python
parts: list[Part]

```

The parts of the message.

#### kind

```python
kind: Literal['message']

```

Event type.

#### metadata

```python
metadata: NotRequired[dict[str, Any]]

```

Metadata about the message.

#### message_id

```python
message_id: str

```

Identifier created by the message creator.

#### context_id

```python
context_id: NotRequired[str]

```

The context the message is associated with.

#### task_id

```python
task_id: NotRequired[str]

```

Identifier of task the message is related to.

#### reference_task_ids

```python
reference_task_ids: NotRequired[list[str]]

```

Array of task IDs this message references.

#### extensions

```python
extensions: NotRequired[list[str]]

```

Array of extensions.
