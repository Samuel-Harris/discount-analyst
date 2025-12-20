### EvaluationReason

The result of running an evaluator with an optional explanation.

Contains a scalar value and an optional "reason" explaining the value.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `value` | `EvaluationScalar` | The scalar result of the evaluation (boolean, integer, float, or string). | _required_ | | `reason` | `str | None` | An optional explanation of the evaluation result. | `None` |

Source code in `pydantic_evals/pydantic_evals/evaluators/evaluator.py`

```python
@dataclass
class EvaluationReason:
    """The result of running an evaluator with an optional explanation.

    Contains a scalar value and an optional "reason" explaining the value.

    Args:
        value: The scalar result of the evaluation (boolean, integer, float, or string).
        reason: An optional explanation of the evaluation result.
    """

    value: EvaluationScalar
    reason: str | None = None

```
