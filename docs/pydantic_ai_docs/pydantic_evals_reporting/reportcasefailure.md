### ReportCaseFailure

Bases: `Generic[InputsT, OutputT, MetadataT]`

A single case in an evaluation report that failed due to an error during task execution.

Source code in `pydantic_evals/pydantic_evals/reporting/__init__.py`

```python
@dataclass(kw_only=True)
class ReportCaseFailure(Generic[InputsT, OutputT, MetadataT]):
    """A single case in an evaluation report that failed due to an error during task execution."""

    name: str
    """The name of the [case][pydantic_evals.Case]."""
    inputs: InputsT
    """The inputs to the task, from [`Case.inputs`][pydantic_evals.Case.inputs]."""
    metadata: MetadataT | None
    """Any metadata associated with the case, from [`Case.metadata`][pydantic_evals.Case.metadata]."""
    expected_output: OutputT | None
    """The expected output of the task, from [`Case.expected_output`][pydantic_evals.Case.expected_output]."""

    error_message: str
    """The message of the exception that caused the failure."""
    error_stacktrace: str
    """The stacktrace of the exception that caused the failure."""

    trace_id: str | None = None
    """The trace ID of the case span."""
    span_id: str | None = None
    """The span ID of the case span."""

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

#### error_message

```python
error_message: str

```

The message of the exception that caused the failure.

#### error_stacktrace

```python
error_stacktrace: str

```

The stacktrace of the exception that caused the failure.

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
