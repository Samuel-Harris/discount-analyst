### IsInstance

Bases: `Evaluator[object, object, object]`

Check if the output is an instance of a type with the given name.

Source code in `pydantic_evals/pydantic_evals/evaluators/common.py`

```python
@dataclass(repr=False)
class IsInstance(Evaluator[object, object, object]):
    """Check if the output is an instance of a type with the given name."""

    type_name: str
    evaluation_name: str | None = field(default=None)

    def evaluate(self, ctx: EvaluatorContext[object, object, object]) -> EvaluationReason:
        output = ctx.output
        for cls in type(output).__mro__:
            if cls.__name__ == self.type_name or cls.__qualname__ == self.type_name:
                return EvaluationReason(value=True)

        reason = f'output is of type {type(output).__name__}'
        if type(output).__qualname__ != type(output).__name__:
            reason += f' (qualname: {type(output).__qualname__})'
        return EvaluationReason(value=False, reason=reason)

```
