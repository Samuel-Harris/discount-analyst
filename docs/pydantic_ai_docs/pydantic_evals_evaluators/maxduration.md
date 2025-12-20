### MaxDuration

Bases: `Evaluator[object, object, object]`

Check if the execution time is under the specified maximum.

Source code in `pydantic_evals/pydantic_evals/evaluators/common.py`

```python
@dataclass(repr=False)
class MaxDuration(Evaluator[object, object, object]):
    """Check if the execution time is under the specified maximum."""

    seconds: float | timedelta

    def evaluate(self, ctx: EvaluatorContext[object, object, object]) -> bool:
        duration = timedelta(seconds=ctx.duration)
        seconds = self.seconds
        if not isinstance(seconds, timedelta):
            seconds = timedelta(seconds=seconds)
        return duration <= seconds

```
