### TaskPushNotificationConfig

Bases: `TypedDict`

Configuration for task push notifications.

Source code in `.venv/lib/python3.12/site-packages/fasta2a/schema.py`

```python
@pydantic.with_config({'alias_generator': to_camel})
class TaskPushNotificationConfig(TypedDict):
    """Configuration for task push notifications."""

    id: str
    """The task id."""

    push_notification_config: PushNotificationConfig
    """The push notification configuration."""

```

#### id

```python
id: str

```

The task id.

#### push_notification_config

```python
push_notification_config: PushNotificationConfig

```

The push notification configuration.
