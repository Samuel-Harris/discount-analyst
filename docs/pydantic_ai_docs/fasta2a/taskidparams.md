### TaskIdParams

Bases: `TypedDict`

Parameters for a task id.

Source code in `.venv/lib/python3.12/site-packages/fasta2a/schema.py`

```python
@pydantic.with_config({'alias_generator': to_camel})
class TaskIdParams(TypedDict):
    """Parameters for a task id."""

    id: str
    metadata: NotRequired[dict[str, Any]]

```
