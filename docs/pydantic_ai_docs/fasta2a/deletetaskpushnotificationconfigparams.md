### DeleteTaskPushNotificationConfigParams

Bases: `TypedDict`

Parameters for removing pushNotificationConfiguration associated with a Task.

Source code in `.venv/lib/python3.12/site-packages/fasta2a/schema.py`

```python
@pydantic.with_config({'alias_generator': to_camel})
class DeleteTaskPushNotificationConfigParams(TypedDict):
    """Parameters for removing pushNotificationConfiguration associated with a Task."""

    id: str
    """Task id."""

    push_notification_config_id: str
    """The push notification config id to delete."""

    metadata: NotRequired[dict[str, Any]]
    """Extension metadata."""

```

#### id

```python
id: str

```

Task id.

#### push_notification_config_id

```python
push_notification_config_id: str

```

The push notification config id to delete.

#### metadata

```python
metadata: NotRequired[dict[str, Any]]

```

Extension metadata.
