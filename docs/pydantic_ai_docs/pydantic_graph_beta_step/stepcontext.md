### StepContext

Bases: `Generic[StateT, DepsT, InputT]`

Context information passed to step functions during graph execution.

The step context provides access to the current graph state, dependencies, and input data for a step.

Type Parameters

StateT: The type of the graph state DepsT: The type of the dependencies InputT: The type of the input data

Source code in `pydantic_graph/pydantic_graph/beta/step.py`

```python
@dataclass(init=False)
class StepContext(Generic[StateT, DepsT, InputT]):
    """Context information passed to step functions during graph execution.

    The step context provides access to the current graph state, dependencies, and input data for a step.

    Type Parameters:
        StateT: The type of the graph state
        DepsT: The type of the dependencies
        InputT: The type of the input data
    """

    _state: StateT
    """The current graph state."""
    _deps: DepsT
    """The graph run dependencies."""
    _inputs: InputT
    """The input data for this step."""

    def __init__(self, *, state: StateT, deps: DepsT, inputs: InputT):
        self._state = state
        self._deps = deps
        self._inputs = inputs

    @property
    def state(self) -> StateT:
        return self._state

    @property
    def deps(self) -> DepsT:
        return self._deps

    @property
    def inputs(self) -> InputT:
        """The input data for this step.

        This must be a property to ensure correct variance behavior
        """
        return self._inputs

```

#### inputs

```python
inputs: InputT

```

The input data for this step.

This must be a property to ensure correct variance behavior
