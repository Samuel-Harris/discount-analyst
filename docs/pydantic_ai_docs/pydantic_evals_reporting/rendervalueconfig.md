### RenderValueConfig

Bases: `TypedDict`

A configuration for rendering a values in an Evaluation report.

Source code in `pydantic_evals/pydantic_evals/reporting/__init__.py`

```python
class RenderValueConfig(TypedDict, total=False):
    """A configuration for rendering a values in an Evaluation report."""

    value_formatter: str | Callable[[Any], str]
    diff_checker: Callable[[Any, Any], bool] | None
    diff_formatter: Callable[[Any, Any], str | None] | None
    diff_style: str

```
