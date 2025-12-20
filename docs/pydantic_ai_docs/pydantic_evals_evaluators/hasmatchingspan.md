### HasMatchingSpan

Bases: `Evaluator[object, object, object]`

Check if the span tree contains a span that matches the specified query.

Source code in `pydantic_evals/pydantic_evals/evaluators/common.py`

```python
@dataclass(repr=False)
class HasMatchingSpan(Evaluator[object, object, object]):
    """Check if the span tree contains a span that matches the specified query."""

    query: SpanQuery
    evaluation_name: str | None = field(default=None)

    def evaluate(
        self,
        ctx: EvaluatorContext[object, object, object],
    ) -> bool:
        return ctx.span_tree.any(self.query)

```
