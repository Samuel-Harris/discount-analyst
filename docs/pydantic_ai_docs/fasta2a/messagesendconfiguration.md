### MessageSendConfiguration

Bases: `TypedDict`

Configuration for the send message request.

Source code in `.venv/lib/python3.12/site-packages/fasta2a/schema.py`

```python
@pydantic.with_config({'alias_generator': to_camel})
class MessageSendConfiguration(TypedDict):
    """Configuration for the send message request."""

    accepted_output_modes: list[str]
    """Accepted output modalities by the client."""

    blocking: NotRequired[bool]
    """If the server should treat the client as a blocking request."""

    history_length: NotRequired[int]
    """Number of recent messages to be retrieved."""

    push_notification_config: NotRequired[PushNotificationConfig]
    """Where the server should send notifications when disconnected."""

```

#### accepted_output_modes

```python
accepted_output_modes: list[str]

```

Accepted output modalities by the client.

#### blocking

```python
blocking: NotRequired[bool]

```

If the server should treat the client as a blocking request.

#### history_length

```python
history_length: NotRequired[int]

```

Number of recent messages to be retrieved.

#### push_notification_config

```python
push_notification_config: NotRequired[
    PushNotificationConfig
]

```

Where the server should send notifications when disconnected.
