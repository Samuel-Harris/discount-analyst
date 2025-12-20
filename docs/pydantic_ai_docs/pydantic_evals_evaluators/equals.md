### Equals

Bases: `Evaluator[object, object, object]`

Check if the output exactly equals the provided value.

Source code in `pydantic_evals/pydantic_evals/evaluators/common.py`

```python
@dataclass(repr=False)
class Equals(Evaluator[object, object, object]):
    """Check if the output exactly equals the provided value."""

    value: Any
    evaluation_name: str | None = field(default=None)

    def evaluate(self, ctx: EvaluatorContext[object, object, object]) -> bool:
        return ctx.output == self.value

```
