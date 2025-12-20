### EvaluatorOutput

```python
EvaluatorOutput = (
    EvaluationScalar
    | EvaluationReason
    | Mapping[str, EvaluationScalar | EvaluationReason]
)

```

Type for the output of an evaluator, which can be a scalar, an EvaluationReason, or a mapping of names to either.
