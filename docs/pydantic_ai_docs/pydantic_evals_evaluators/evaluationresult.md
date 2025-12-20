### EvaluationResult

Bases: `Generic[EvaluationScalarT]`

The details of an individual evaluation result.

Contains the name, value, reason, and source evaluator for a single evaluation.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `name` | `str` | The name of the evaluation. | _required_ | | `value` | `EvaluationScalarT` | The scalar result of the evaluation. | _required_ | | `reason` | `str | None` | An optional explanation of the evaluation result. | _required_ | | `source` | `EvaluatorSpec` | The spec of the evaluator that produced this result. | _required_ |

Source code in `pydantic_evals/pydantic_evals/evaluators/evaluator.py`

```python
@dataclass
class EvaluationResult(Generic[EvaluationScalarT]):
    """The details of an individual evaluation result.

    Contains the name, value, reason, and source evaluator for a single evaluation.

    Args:
        name: The name of the evaluation.
        value: The scalar result of the evaluation.
        reason: An optional explanation of the evaluation result.
        source: The spec of the evaluator that produced this result.
    """

    name: str
    value: EvaluationScalarT
    reason: str | None
    source: EvaluatorSpec

    def downcast(self, *value_types: type[T]) -> EvaluationResult[T] | None:
        """Attempt to downcast this result to a more specific type.

        Args:
            *value_types: The types to check the value against.

        Returns:
            A downcast version of this result if the value is an instance of one of the given types,
            otherwise None.
        """
        # Check if value matches any of the target types, handling bool as a special case
        for value_type in value_types:
            if isinstance(self.value, value_type):
                # Only match bool with explicit bool type
                if isinstance(self.value, bool) and value_type is not bool:
                    continue
                return cast(EvaluationResult[T], self)
        return None

```

#### downcast

```python
downcast(
    *value_types: type[T],
) -> EvaluationResult[T] | None

```

Attempt to downcast this result to a more specific type.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `*value_types` | `type[T]` | The types to check the value against. | `()` |

Returns:

| Type | Description | | --- | --- | | `EvaluationResult[T] | None` | A downcast version of this result if the value is an instance of one of the given types, | | `EvaluationResult[T] | None` | otherwise None. |

Source code in `pydantic_evals/pydantic_evals/evaluators/evaluator.py`

```python
def downcast(self, *value_types: type[T]) -> EvaluationResult[T] | None:
    """Attempt to downcast this result to a more specific type.

    Args:
        *value_types: The types to check the value against.

    Returns:
        A downcast version of this result if the value is an instance of one of the given types,
        otherwise None.
    """
    # Check if value matches any of the target types, handling bool as a special case
    for value_type in value_types:
        if isinstance(self.value, value_type):
            # Only match bool with explicit bool type
            if isinstance(self.value, bool) and value_type is not bool:
                continue
            return cast(EvaluationResult[T], self)
    return None

```
