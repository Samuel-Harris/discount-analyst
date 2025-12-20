### increment_eval_metric

```python
increment_eval_metric(
    name: str, amount: int | float
) -> None

```

Increment a metric on the current task run.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `name` | `str` | The name of the metric. | _required_ | | `amount` | `int | float` | The amount to increment by. | _required_ |

Source code in `pydantic_evals/pydantic_evals/dataset.py`

```python
def increment_eval_metric(name: str, amount: int | float) -> None:
    """Increment a metric on the current task run.

    Args:
        name: The name of the metric.
        amount: The amount to increment by.
    """
    current_case = _CURRENT_TASK_RUN.get()
    if current_case is not None:  # pragma: no branch
        current_case.increment_metric(name, amount)

```
