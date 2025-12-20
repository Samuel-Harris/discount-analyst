### ListTaskPushNotificationConfigParams

Bases: `TypedDict`

Parameters for getting list of pushNotificationConfigurations associated with a Task.

Source code in `.venv/lib/python3.12/site-packages/fasta2a/schema.py`

```python
@pydantic.with_config({'alias_generator': to_camel})
class ListTaskPushNotificationConfigParams(TypedDict):
    """Parameters for getting list of pushNotificationConfigurations associated with a Task."""

    id: str
    """Task id."""

    metadata: NotRequired[dict[str, Any]]
    """Extension metadata."""

```

#### id

```python
id: str

```

Task id.

#### metadata

```python
metadata: NotRequired[dict[str, Any]]

```

Extension metadata.
