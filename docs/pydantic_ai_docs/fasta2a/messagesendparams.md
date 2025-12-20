### MessageSendParams

Bases: `TypedDict`

Parameters for message/send method.

Source code in `.venv/lib/python3.12/site-packages/fasta2a/schema.py`

```python
@pydantic.with_config({'alias_generator': to_camel})
class MessageSendParams(TypedDict):
    """Parameters for message/send method."""

    configuration: NotRequired[MessageSendConfiguration]
    """Send message configuration."""

    message: Message
    """The message being sent to the server."""

    metadata: NotRequired[dict[str, Any]]
    """Extension metadata."""

```

#### configuration

```python
configuration: NotRequired[MessageSendConfiguration]

```

Send message configuration.

#### message

```python
message: Message

```

The message being sent to the server.

#### metadata

```python
metadata: NotRequired[dict[str, Any]]

```

Extension metadata.
