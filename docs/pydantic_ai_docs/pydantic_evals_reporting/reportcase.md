### ReportCase

Bases: `Generic[InputsT, OutputT, MetadataT]`

A single case in an evaluation report.

Source code in `pydantic_evals/pydantic_evals/reporting/__init__.py`

```python
@dataclass(kw_only=True)
class ReportCase(Generic[InputsT, OutputT, MetadataT]):
    """A single case in an evaluation report."""

    name: str
    """The name of the [case][pydantic_evals.Case]."""
    inputs: InputsT
    """The inputs to the task, from [`Case.inputs`][pydantic_evals.Case.inputs]."""
    metadata: MetadataT | None
    """Any metadata associated with the case, from [`Case.metadata`][pydantic_evals.Case.metadata]."""
    expected_output: OutputT | None
    """The expected output of the task, from [`Case.expected_output`][pydantic_evals.Case.expected_output]."""
    output: OutputT
    """The output of the task execution."""

    metrics: dict[str, float | int]
    attributes: dict[str, Any]

    scores: dict[str, EvaluationResult[int | float]]
    labels: dict[str, EvaluationResult[str]]
    assertions: dict[str, EvaluationResult[bool]]

    task_duration: float
    total_duration: float  # includes evaluator execution time

    trace_id: str | None = None
    """The trace ID of the case span."""
    span_id: str | None = None
    """The span ID of the case span."""

    evaluator_failures: list[EvaluatorFailure] = field(default_factory=list)

```

#### name

```python
name: str

```

The name of the case.

#### inputs

```python
inputs: InputsT

```

The inputs to the task, from Case.inputs.

#### metadata

```python
metadata: MetadataT | None

```

Any metadata associated with the case, from Case.metadata.

#### expected_output

```python
expected_output: OutputT | None

```

The expected output of the task, from Case.expected_output.

#### output

```python
output: OutputT

```

The output of the task execution.

#### trace_id

```python
trace_id: str | None = None

```

The trace ID of the case span.

#### span_id

```python
span_id: str | None = None

```

The span ID of the case span.
