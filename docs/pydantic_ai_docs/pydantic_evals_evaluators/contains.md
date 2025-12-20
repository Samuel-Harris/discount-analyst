### Contains

Bases: `Evaluator[object, object, object]`

Check if the output contains the expected output.

For strings, checks if expected_output is a substring of output. For lists/tuples, checks if expected_output is in output. For dicts, checks if all key-value pairs in expected_output are in output.

Note: case_sensitive only applies when both the value and output are strings.

Source code in `pydantic_evals/pydantic_evals/evaluators/common.py`

```python
@dataclass(repr=False)
class Contains(Evaluator[object, object, object]):
    """Check if the output contains the expected output.

    For strings, checks if expected_output is a substring of output.
    For lists/tuples, checks if expected_output is in output.
    For dicts, checks if all key-value pairs in expected_output are in output.

    Note: case_sensitive only applies when both the value and output are strings.
    """

    value: Any
    case_sensitive: bool = True
    as_strings: bool = False
    evaluation_name: str | None = field(default=None)

    def evaluate(
        self,
        ctx: EvaluatorContext[object, object, object],
    ) -> EvaluationReason:
        # Convert objects to strings if requested
        failure_reason: str | None = None
        as_strings = self.as_strings or (isinstance(self.value, str) and isinstance(ctx.output, str))
        if as_strings:
            output_str = str(ctx.output)
            expected_str = str(self.value)

            if not self.case_sensitive:
                output_str = output_str.lower()
                expected_str = expected_str.lower()

            failure_reason: str | None = None
            if expected_str not in output_str:
                output_trunc = _truncated_repr(output_str, max_length=100)
                expected_trunc = _truncated_repr(expected_str, max_length=100)
                failure_reason = f'Output string {output_trunc} does not contain expected string {expected_trunc}'
            return EvaluationReason(value=failure_reason is None, reason=failure_reason)

        try:
            # Handle different collection types
            if isinstance(ctx.output, dict):
                if isinstance(self.value, dict):
                    # Cast to Any to avoid type checking issues
                    output_dict = cast(dict[Any, Any], ctx.output)  # pyright: ignore[reportUnknownMemberType]
                    expected_dict = cast(dict[Any, Any], self.value)  # pyright: ignore[reportUnknownMemberType]
                    for k in expected_dict:
                        if k not in output_dict:
                            k_trunc = _truncated_repr(k, max_length=30)
                            failure_reason = f'Output dictionary does not contain expected key {k_trunc}'
                            break
                        elif output_dict[k] != expected_dict[k]:
                            k_trunc = _truncated_repr(k, max_length=30)
                            output_v_trunc = _truncated_repr(output_dict[k], max_length=100)
                            expected_v_trunc = _truncated_repr(expected_dict[k], max_length=100)
                            failure_reason = f'Output dictionary has different value for key {k_trunc}: {output_v_trunc} != {expected_v_trunc}'
                            break
                else:
                    if self.value not in ctx.output:  # pyright: ignore[reportUnknownMemberType]
                        output_trunc = _truncated_repr(ctx.output, max_length=200)  # pyright: ignore[reportUnknownMemberType]
                        failure_reason = f'Output {output_trunc} does not contain provided value as a key'
            elif self.value not in ctx.output:  # pyright: ignore[reportOperatorIssue]  # will be handled by except block
                output_trunc = _truncated_repr(ctx.output, max_length=200)
                failure_reason = f'Output {output_trunc} does not contain provided value'
        except (TypeError, ValueError) as e:
            failure_reason = f'Containment check failed: {e}'

        return EvaluationReason(value=failure_reason is None, reason=failure_reason)

```
