### TaskQueryParams

Bases: `TaskIdParams`

Query parameters for a task.

Source code in `.venv/lib/python3.12/site-packages/fasta2a/schema.py`

```python
@pydantic.with_config({'alias_generator': to_camel})
class TaskQueryParams(TaskIdParams):
    """Query parameters for a task."""

    history_length: NotRequired[int]
    """Number of recent messages to be retrieved."""

```

#### history_length

```python
history_length: NotRequired[int]

```

Number of recent messages to be retrieved.
