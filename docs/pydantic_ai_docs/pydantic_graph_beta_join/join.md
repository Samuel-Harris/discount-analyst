### Join

Bases: `Generic[StateT, DepsT, InputT, OutputT]`

A join operation that synchronizes and aggregates parallel execution paths.

A join defines how to combine outputs from multiple parallel execution paths using a ReducerFunction. It specifies which fork it joins (if any) and manages the initialization of reducers.

Type Parameters

StateT: The type of the graph state DepsT: The type of the dependencies InputT: The type of input data to join OutputT: The type of the final joined output

Source code in `pydantic_graph/pydantic_graph/beta/join.py`

```python
@dataclass(init=False)
class Join(Generic[StateT, DepsT, InputT, OutputT]):
    """A join operation that synchronizes and aggregates parallel execution paths.

    A join defines how to combine outputs from multiple parallel execution paths
    using a [`ReducerFunction`][pydantic_graph.beta.join.ReducerFunction]. It specifies which fork
    it joins (if any) and manages the initialization of reducers.

    Type Parameters:
        StateT: The type of the graph state
        DepsT: The type of the dependencies
        InputT: The type of input data to join
        OutputT: The type of the final joined output
    """

    id: JoinID
    _reducer: ReducerFunction[StateT, DepsT, InputT, OutputT]
    _initial_factory: Callable[[], OutputT]
    parent_fork_id: ForkID | None
    preferred_parent_fork: Literal['closest', 'farthest']

    def __init__(
        self,
        *,
        id: JoinID,
        reducer: ReducerFunction[StateT, DepsT, InputT, OutputT],
        initial_factory: Callable[[], OutputT],
        parent_fork_id: ForkID | None = None,
        preferred_parent_fork: Literal['farthest', 'closest'] = 'farthest',
    ):
        self.id = id
        self._reducer = reducer
        self._initial_factory = initial_factory
        self.parent_fork_id = parent_fork_id
        self.preferred_parent_fork = preferred_parent_fork

    @property
    def reducer(self):
        return self._reducer

    @property
    def initial_factory(self):
        return self._initial_factory

    def reduce(self, ctx: ReducerContext[StateT, DepsT], current: OutputT, inputs: InputT) -> OutputT:
        n_parameters = len(inspect.signature(self.reducer).parameters)
        if n_parameters == 2:
            return cast(PlainReducerFunction[InputT, OutputT], self.reducer)(current, inputs)
        else:
            return cast(ContextReducerFunction[StateT, DepsT, InputT, OutputT], self.reducer)(ctx, current, inputs)

    @overload
    def as_node(self, inputs: None = None) -> JoinNode[StateT, DepsT]: ...

    @overload
    def as_node(self, inputs: InputT) -> JoinNode[StateT, DepsT]: ...

    def as_node(self, inputs: InputT | None = None) -> JoinNode[StateT, DepsT]:
        """Create a step node with bound inputs.

        Args:
            inputs: The input data to bind to this step, or None

        Returns:
            A [`StepNode`][pydantic_graph.beta.step.StepNode] with this step and the bound inputs
        """
        return JoinNode(self, inputs)

```

#### as_node

```python
as_node(inputs: None = None) -> JoinNode[StateT, DepsT]

```

```python
as_node(inputs: InputT) -> JoinNode[StateT, DepsT]

```

```python
as_node(
    inputs: InputT | None = None,
) -> JoinNode[StateT, DepsT]

```

Create a step node with bound inputs.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `inputs` | `InputT | None` | The input data to bind to this step, or None | `None` |

Returns:

| Type | Description | | --- | --- | | `JoinNode[StateT, DepsT]` | A StepNode with this step and the bound inputs |

Source code in `pydantic_graph/pydantic_graph/beta/join.py`

```python
def as_node(self, inputs: InputT | None = None) -> JoinNode[StateT, DepsT]:
    """Create a step node with bound inputs.

    Args:
        inputs: The input data to bind to this step, or None

    Returns:
        A [`StepNode`][pydantic_graph.beta.step.StepNode] with this step and the bound inputs
    """
    return JoinNode(self, inputs)

```
