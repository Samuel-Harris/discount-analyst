### EqualsExpected

Bases: `Evaluator[object, object, object]`

Check if the output exactly equals the expected output.

Source code in `pydantic_evals/pydantic_evals/evaluators/common.py`

```python
@dataclass(repr=False)
class EqualsExpected(Evaluator[object, object, object]):
    """Check if the output exactly equals the expected output."""

    evaluation_name: str | None = field(default=None)

    def evaluate(self, ctx: EvaluatorContext[object, object, object]) -> bool | dict[str, bool]:
        if ctx.expected_output is None:
            return {}  # Only compare if expected output is provided
        return ctx.output == ctx.expected_output

```
