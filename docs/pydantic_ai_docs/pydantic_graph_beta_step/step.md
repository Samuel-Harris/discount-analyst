### Step

Bases: `Generic[StateT, DepsT, InputT, OutputT]`

A step in the graph execution that wraps a step function.

Steps represent individual units of execution in the graph, encapsulating a step function along with metadata like ID and label.

Type Parameters

StateT: The type of the graph state DepsT: The type of the dependencies InputT: The type of the input data OutputT: The type of the output data

Source code in `pydantic_graph/pydantic_graph/beta/step.py`

```python
@dataclass(init=False)
class Step(Generic[StateT, DepsT, InputT, OutputT]):
    """A step in the graph execution that wraps a step function.

    Steps represent individual units of execution in the graph, encapsulating
    a step function along with metadata like ID and label.

    Type Parameters:
        StateT: The type of the graph state
        DepsT: The type of the dependencies
        InputT: The type of the input data
        OutputT: The type of the output data
    """

    id: NodeID
    """Unique identifier for this step."""
    _call: StepFunction[StateT, DepsT, InputT, OutputT]
    """The step function to execute."""
    label: str | None
    """Optional human-readable label for this step."""

    def __init__(self, *, id: NodeID, call: StepFunction[StateT, DepsT, InputT, OutputT], label: str | None = None):
        self.id = id
        self._call = call
        self.label = label

    @property
    def call(self) -> StepFunction[StateT, DepsT, InputT, OutputT]:
        """The step function to execute. This needs to be a property for proper variance inference."""
        return self._call

    @overload
    def as_node(self, inputs: None = None) -> StepNode[StateT, DepsT]: ...

    @overload
    def as_node(self, inputs: InputT) -> StepNode[StateT, DepsT]: ...

    def as_node(self, inputs: InputT | None = None) -> StepNode[StateT, DepsT]:
        """Create a step node with bound inputs.

        Args:
            inputs: The input data to bind to this step, or None

        Returns:
            A [`StepNode`][pydantic_graph.beta.step.StepNode] with this step and the bound inputs
        """
        return StepNode(self, inputs)

```

#### id

```python
id: NodeID = id

```

Unique identifier for this step.

#### label

```python
label: str | None = label

```

Optional human-readable label for this step.

#### call

```python
call: StepFunction[StateT, DepsT, InputT, OutputT]

```

The step function to execute. This needs to be a property for proper variance inference.

#### as_node

```python
as_node(inputs: None = None) -> StepNode[StateT, DepsT]

```

```python
as_node(inputs: InputT) -> StepNode[StateT, DepsT]

```

```python
as_node(
    inputs: InputT | None = None,
) -> StepNode[StateT, DepsT]

```

Create a step node with bound inputs.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `inputs` | `InputT | None` | The input data to bind to this step, or None | `None` |

Returns:

| Type | Description | | --- | --- | | `StepNode[StateT, DepsT]` | A StepNode with this step and the bound inputs |

Source code in `pydantic_graph/pydantic_graph/beta/step.py`

```python
def as_node(self, inputs: InputT | None = None) -> StepNode[StateT, DepsT]:
    """Create a step node with bound inputs.

    Args:
        inputs: The input data to bind to this step, or None

    Returns:
        A [`StepNode`][pydantic_graph.beta.step.StepNode] with this step and the bound inputs
    """
    return StepNode(self, inputs)

```
