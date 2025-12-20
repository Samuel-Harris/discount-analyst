### ReducerContext

Bases: `Generic[StateT, DepsT]`

Context information passed to reducer functions during graph execution.

The reducer context provides access to the current graph state and dependencies.

Type Parameters

StateT: The type of the graph state DepsT: The type of the dependencies

Source code in `pydantic_graph/pydantic_graph/beta/join.py`

```python
@dataclass(init=False)
class ReducerContext(Generic[StateT, DepsT]):
    """Context information passed to reducer functions during graph execution.

    The reducer context provides access to the current graph state and dependencies.

    Type Parameters:
        StateT: The type of the graph state
        DepsT: The type of the dependencies
    """

    _state: StateT
    """The current graph state."""
    _deps: DepsT
    """The dependencies of the current graph run."""
    _join_state: JoinState
    """The JoinState for this reducer context."""

    def __init__(self, *, state: StateT, deps: DepsT, join_state: JoinState):
        self._state = state
        self._deps = deps
        self._join_state = join_state

    @property
    def state(self) -> StateT:
        """The state of the graph run."""
        return self._state

    @property
    def deps(self) -> DepsT:
        """The deps for the graph run."""
        return self._deps

    def cancel_sibling_tasks(self):
        """Cancel all sibling tasks created from the same fork.

        You can call this if you want your join to have early-stopping behavior.
        """
        self._join_state.cancelled_sibling_tasks = True

```

#### state

```python
state: StateT

```

The state of the graph run.

#### deps

```python
deps: DepsT

```

The deps for the graph run.

#### cancel_sibling_tasks

```python
cancel_sibling_tasks()

```

Cancel all sibling tasks created from the same fork.

You can call this if you want your join to have early-stopping behavior.

Source code in `pydantic_graph/pydantic_graph/beta/join.py`

```python
def cancel_sibling_tasks(self):
    """Cancel all sibling tasks created from the same fork.

    You can call this if you want your join to have early-stopping behavior.
    """
    self._join_state.cancelled_sibling_tasks = True

```
