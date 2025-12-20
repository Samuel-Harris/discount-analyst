### set_eval_attribute

```python
set_eval_attribute(name: str, value: Any) -> None

```

Set an attribute on the current task run.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `name` | `str` | The name of the attribute. | _required_ | | `value` | `Any` | The value of the attribute. | _required_ |

Source code in `pydantic_evals/pydantic_evals/dataset.py`

```python
def set_eval_attribute(name: str, value: Any) -> None:
    """Set an attribute on the current task run.

    Args:
        name: The name of the attribute.
        value: The value of the attribute.
    """
    current_case = _CURRENT_TASK_RUN.get()
    if current_case is not None:  # pragma: no branch
        current_case.record_attribute(name, value)

```
