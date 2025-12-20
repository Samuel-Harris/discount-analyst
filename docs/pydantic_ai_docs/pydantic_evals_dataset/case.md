### Case

Bases: `Generic[InputsT, OutputT, MetadataT]`

A single row of a Dataset.

Each case represents a single test scenario with inputs to test. A case may optionally specify a name, expected outputs to compare against, and arbitrary metadata.

Cases can also have their own specific evaluators which are run in addition to dataset-level evaluators.

Example:

```python
from pydantic_evals import Case

case = Case(
    name='Simple addition',
    inputs={'a': 1, 'b': 2},
    expected_output=3,
    metadata={'description': 'Tests basic addition'},
)

```

Source code in `pydantic_evals/pydantic_evals/dataset.py`

````python
@dataclass(init=False)
class Case(Generic[InputsT, OutputT, MetadataT]):
    """A single row of a [`Dataset`][pydantic_evals.Dataset].

    Each case represents a single test scenario with inputs to test. A case may optionally specify a name, expected
    outputs to compare against, and arbitrary metadata.

    Cases can also have their own specific evaluators which are run in addition to dataset-level evaluators.

    Example:
    ```python
    from pydantic_evals import Case

    case = Case(
        name='Simple addition',
        inputs={'a': 1, 'b': 2},
        expected_output=3,
        metadata={'description': 'Tests basic addition'},
    )
    ```
    """

    name: str | None
    """Name of the case. This is used to identify the case in the report and can be used to filter cases."""
    inputs: InputsT
    """Inputs to the task. This is the input to the task that will be evaluated."""
    metadata: MetadataT | None = None
    """Metadata to be used in the evaluation.

    This can be used to provide additional information about the case to the evaluators.
    """
    expected_output: OutputT | None = None
    """Expected output of the task. This is the expected output of the task that will be evaluated."""
    evaluators: list[Evaluator[InputsT, OutputT, MetadataT]] = field(default_factory=list)
    """Evaluators to be used just on this case."""

    def __init__(
        self,
        *,
        name: str | None = None,
        inputs: InputsT,
        metadata: MetadataT | None = None,
        expected_output: OutputT | None = None,
        evaluators: tuple[Evaluator[InputsT, OutputT, MetadataT], ...] = (),
    ):
        """Initialize a new test case.

        Args:
            name: Optional name for the case. If not provided, a generic name will be assigned when added to a dataset.
            inputs: The inputs to the task being evaluated.
            metadata: Optional metadata for the case, which can be used by evaluators.
            expected_output: Optional expected output of the task, used for comparison in evaluators.
            evaluators: Tuple of evaluators specific to this case. These are in addition to any
                dataset-level evaluators.

        """
        # Note: `evaluators` must be a tuple instead of Sequence due to misbehavior with pyright's generic parameter
        # inference if it has type `Sequence`
        self.name = name
        self.inputs = inputs
        self.metadata = metadata
        self.expected_output = expected_output
        self.evaluators = list(evaluators)

````

#### **init**

```python
__init__(
    *,
    name: str | None = None,
    inputs: InputsT,
    metadata: MetadataT | None = None,
    expected_output: OutputT | None = None,
    evaluators: tuple[
        Evaluator[InputsT, OutputT, MetadataT], ...
    ] = ()
)

```

Initialize a new test case.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `name` | `str | None` | Optional name for the case. If not provided, a generic name will be assigned when added to a dataset. | `None` | | `inputs` | `InputsT` | The inputs to the task being evaluated. | _required_ | | `metadata` | `MetadataT | None` | Optional metadata for the case, which can be used by evaluators. | `None` | | `expected_output` | `OutputT | None` | Optional expected output of the task, used for comparison in evaluators. | `None` | | `evaluators` | `tuple[Evaluator[InputsT, OutputT, MetadataT], ...]` | Tuple of evaluators specific to this case. These are in addition to any dataset-level evaluators. | `()` |

Source code in `pydantic_evals/pydantic_evals/dataset.py`

```python
def __init__(
    self,
    *,
    name: str | None = None,
    inputs: InputsT,
    metadata: MetadataT | None = None,
    expected_output: OutputT | None = None,
    evaluators: tuple[Evaluator[InputsT, OutputT, MetadataT], ...] = (),
):
    """Initialize a new test case.

    Args:
        name: Optional name for the case. If not provided, a generic name will be assigned when added to a dataset.
        inputs: The inputs to the task being evaluated.
        metadata: Optional metadata for the case, which can be used by evaluators.
        expected_output: Optional expected output of the task, used for comparison in evaluators.
        evaluators: Tuple of evaluators specific to this case. These are in addition to any
            dataset-level evaluators.

    """
    # Note: `evaluators` must be a tuple instead of Sequence due to misbehavior with pyright's generic parameter
    # inference if it has type `Sequence`
    self.name = name
    self.inputs = inputs
    self.metadata = metadata
    self.expected_output = expected_output
    self.evaluators = list(evaluators)

```

#### name

```python
name: str | None = name

```

Name of the case. This is used to identify the case in the report and can be used to filter cases.

#### inputs

```python
inputs: InputsT = inputs

```

Inputs to the task. This is the input to the task that will be evaluated.

#### metadata

```python
metadata: MetadataT | None = metadata

```

Metadata to be used in the evaluation.

This can be used to provide additional information about the case to the evaluators.

#### expected_output

```python
expected_output: OutputT | None = expected_output

```

Expected output of the task. This is the expected output of the task that will be evaluated.

#### evaluators

```python
evaluators: list[Evaluator[InputsT, OutputT, MetadataT]] = (
    list(evaluators)
)

```

Evaluators to be used just on this case.
