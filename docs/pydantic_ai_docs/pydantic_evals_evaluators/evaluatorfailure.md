### EvaluatorFailure

Represents a failure raised during the execution of an evaluator.

Source code in `pydantic_evals/pydantic_evals/evaluators/evaluator.py`

```python
@dataclass
class EvaluatorFailure:
    """Represents a failure raised during the execution of an evaluator."""

    name: str
    error_message: str
    error_stacktrace: str
    source: EvaluatorSpec

```
