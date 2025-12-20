### Graph

Bases: `Generic[StateT, DepsT, InputT, OutputT]`

A complete graph definition ready for execution.

The Graph class represents a complete workflow graph with typed inputs, outputs, state, and dependencies. It contains all nodes, edges, and metadata needed for execution.

Type Parameters

StateT: The type of the graph state DepsT: The type of the dependencies InputT: The type of the input data OutputT: The type of the output data

Source code in `pydantic_graph/pydantic_graph/beta/graph.py`

```python
@dataclass(repr=False)
class Graph(Generic[StateT, DepsT, InputT, OutputT]):
    """A complete graph definition ready for execution.

    The Graph class represents a complete workflow graph with typed inputs,
    outputs, state, and dependencies. It contains all nodes, edges, and
    metadata needed for execution.

    Type Parameters:
        StateT: The type of the graph state
        DepsT: The type of the dependencies
        InputT: The type of the input data
        OutputT: The type of the output data
    """

    name: str | None
    """Optional name for the graph, if not provided the name will be inferred from the calling frame on the first call to a graph method."""

    state_type: type[StateT]
    """The type of the graph state."""

    deps_type: type[DepsT]
    """The type of the dependencies."""

    input_type: type[InputT]
    """The type of the input data."""

    output_type: type[OutputT]
    """The type of the output data."""

    auto_instrument: bool
    """Whether to automatically create instrumentation spans."""

    nodes: dict[NodeID, AnyNode]
    """All nodes in the graph indexed by their ID."""

    edges_by_source: dict[NodeID, list[Path]]
    """Outgoing paths from each source node."""

    parent_forks: dict[JoinID, ParentFork[NodeID]]
    """Parent fork information for each join node."""

    intermediate_join_nodes: dict[JoinID, set[JoinID]]
    """For each join, the set of other joins that appear between it and its parent fork.

    Used to determine which joins are "final" (have no other joins as intermediates) and
    which joins should preserve fork stacks when proceeding downstream."""

    def get_parent_fork(self, join_id: JoinID) -> ParentFork[NodeID]:
        """Get the parent fork information for a join node.

        Args:
            join_id: The ID of the join node

        Returns:
            The parent fork information for the join

        Raises:
            RuntimeError: If the join ID is not found or has no parent fork
        """
        result = self.parent_forks.get(join_id)
        if result is None:
            raise RuntimeError(f'Node {join_id} is not a join node or did not have a dominating fork (this is a bug)')
        return result

    def is_final_join(self, join_id: JoinID) -> bool:
        """Check if a join is 'final' (has no downstream joins with the same parent fork).

        A join is non-final if it appears as an intermediate node for another join
        with the same parent fork.

        Args:
            join_id: The ID of the join node

        Returns:
            True if the join is final, False if it's non-final
        """
        # Check if this join appears in any other join's intermediate_join_nodes
        for intermediate_joins in self.intermediate_join_nodes.values():
            if join_id in intermediate_joins:
                return False
        return True

    async def run(
        self,
        *,
        state: StateT = None,
        deps: DepsT = None,
        inputs: InputT = None,
        span: AbstractContextManager[AbstractSpan] | None = None,
        infer_name: bool = True,
    ) -> OutputT:
        """Execute the graph and return the final output.

        This is the main entry point for graph execution. It runs the graph
        to completion and returns the final output value.

        Args:
            state: The graph state instance
            deps: The dependencies instance
            inputs: The input data for the graph
            span: Optional span for tracing/instrumentation
            infer_name: Whether to infer the graph name from the calling frame.

        Returns:
            The final output from the graph execution
        """
        if infer_name and self.name is None:
            inferred_name = infer_obj_name(self, depth=2)
            if inferred_name is not None:  # pragma: no branch
                self.name = inferred_name

        async with self.iter(state=state, deps=deps, inputs=inputs, span=span, infer_name=False) as graph_run:
            # Note: This would probably be better using `async for _ in graph_run`, but this tests the `next` method,
            # which I'm less confident will be implemented correctly if not used on the critical path. We can change it
            # once we have tests, etc.
            event: Any = None
            while True:
                try:
                    event = await graph_run.next(event)
                except StopAsyncIteration:
                    assert isinstance(event, EndMarker), 'Graph run should end with an EndMarker.'
                    return cast(EndMarker[OutputT], event).value

    @asynccontextmanager
    async def iter(
        self,
        *,
        state: StateT = None,
        deps: DepsT = None,
        inputs: InputT = None,
        span: AbstractContextManager[AbstractSpan] | None = None,
        infer_name: bool = True,
    ) -> AsyncIterator[GraphRun[StateT, DepsT, OutputT]]:
        """Create an iterator for step-by-step graph execution.

        This method allows for more fine-grained control over graph execution,
        enabling inspection of intermediate states and results.

        Args:
            state: The graph state instance
            deps: The dependencies instance
            inputs: The input data for the graph
            span: Optional span for tracing/instrumentation
            infer_name: Whether to infer the graph name from the calling frame.

        Yields:
            A GraphRun instance that can be iterated for step-by-step execution
        """
        if infer_name and self.name is None:
            inferred_name = infer_obj_name(self, depth=3)  # depth=3 because asynccontextmanager adds one
            if inferred_name is not None:  # pragma: no branch
                self.name = inferred_name

        with ExitStack() as stack:
            entered_span: AbstractSpan | None = None
            if span is None:
                if self.auto_instrument:
                    entered_span = stack.enter_context(logfire_span('run graph {graph.name}', graph=self))
            else:
                entered_span = stack.enter_context(span)
            traceparent = None if entered_span is None else get_traceparent(entered_span)
            async with GraphRun[StateT, DepsT, OutputT](
                graph=self,
                state=state,
                deps=deps,
                inputs=inputs,
                traceparent=traceparent,
            ) as graph_run:
                yield graph_run

    def render(self, *, title: str | None = None, direction: StateDiagramDirection | None = None) -> str:
        """Render the graph as a Mermaid diagram string.

        Args:
            title: Optional title for the diagram
            direction: Optional direction for the diagram layout

        Returns:
            A string containing the Mermaid diagram representation
        """
        from pydantic_graph.beta.mermaid import build_mermaid_graph

        return build_mermaid_graph(self.nodes, self.edges_by_source).render(title=title, direction=direction)

    def __repr__(self) -> str:
        super_repr = super().__repr__()  # include class and memory address
        # Insert the result of calling `__str__` before the final '>' in the repr
        return f'{super_repr[:-1]}\n{self}\n{super_repr[-1]}'

    def __str__(self) -> str:
        """Return a Mermaid diagram representation of the graph.

        Returns:
            A string containing the Mermaid diagram of the graph
        """
        return self.render()

```

#### name

```python
name: str | None

```

Optional name for the graph, if not provided the name will be inferred from the calling frame on the first call to a graph method.

#### state_type

```python
state_type: type[StateT]

```

The type of the graph state.

#### deps_type

```python
deps_type: type[DepsT]

```

The type of the dependencies.

#### input_type

```python
input_type: type[InputT]

```

The type of the input data.

#### output_type

```python
output_type: type[OutputT]

```

The type of the output data.

#### auto_instrument

```python
auto_instrument: bool

```

Whether to automatically create instrumentation spans.

#### nodes

```python
nodes: dict[NodeID, AnyNode]

```

All nodes in the graph indexed by their ID.

#### edges_by_source

```python
edges_by_source: dict[NodeID, list[Path]]

```

Outgoing paths from each source node.

#### parent_forks

```python
parent_forks: dict[JoinID, ParentFork[NodeID]]

```

Parent fork information for each join node.

#### intermediate_join_nodes

```python
intermediate_join_nodes: dict[JoinID, set[JoinID]]

```

For each join, the set of other joins that appear between it and its parent fork.

Used to determine which joins are "final" (have no other joins as intermediates) and which joins should preserve fork stacks when proceeding downstream.

#### get_parent_fork

```python
get_parent_fork(join_id: JoinID) -> ParentFork[NodeID]

```

Get the parent fork information for a join node.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `join_id` | `JoinID` | The ID of the join node | _required_ |

Returns:

| Type | Description | | --- | --- | | `ParentFork[NodeID]` | The parent fork information for the join |

Raises:

| Type | Description | | --- | --- | | `RuntimeError` | If the join ID is not found or has no parent fork |

Source code in `pydantic_graph/pydantic_graph/beta/graph.py`

```python
def get_parent_fork(self, join_id: JoinID) -> ParentFork[NodeID]:
    """Get the parent fork information for a join node.

    Args:
        join_id: The ID of the join node

    Returns:
        The parent fork information for the join

    Raises:
        RuntimeError: If the join ID is not found or has no parent fork
    """
    result = self.parent_forks.get(join_id)
    if result is None:
        raise RuntimeError(f'Node {join_id} is not a join node or did not have a dominating fork (this is a bug)')
    return result

```

#### is_final_join

```python
is_final_join(join_id: JoinID) -> bool

```

Check if a join is 'final' (has no downstream joins with the same parent fork).

A join is non-final if it appears as an intermediate node for another join with the same parent fork.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `join_id` | `JoinID` | The ID of the join node | _required_ |

Returns:

| Type | Description | | --- | --- | | `bool` | True if the join is final, False if it's non-final |

Source code in `pydantic_graph/pydantic_graph/beta/graph.py`

```python
def is_final_join(self, join_id: JoinID) -> bool:
    """Check if a join is 'final' (has no downstream joins with the same parent fork).

    A join is non-final if it appears as an intermediate node for another join
    with the same parent fork.

    Args:
        join_id: The ID of the join node

    Returns:
        True if the join is final, False if it's non-final
    """
    # Check if this join appears in any other join's intermediate_join_nodes
    for intermediate_joins in self.intermediate_join_nodes.values():
        if join_id in intermediate_joins:
            return False
    return True

```

#### run

```python
run(
    *,
    state: StateT = None,
    deps: DepsT = None,
    inputs: InputT = None,
    span: (
        AbstractContextManager[AbstractSpan] | None
    ) = None,
    infer_name: bool = True
) -> OutputT

```

Execute the graph and return the final output.

This is the main entry point for graph execution. It runs the graph to completion and returns the final output value.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `state` | `StateT` | The graph state instance | `None` | | `deps` | `DepsT` | The dependencies instance | `None` | | `inputs` | `InputT` | The input data for the graph | `None` | | `span` | `AbstractContextManager[AbstractSpan] | None` | Optional span for tracing/instrumentation | `None` | | `infer_name` | `bool` | Whether to infer the graph name from the calling frame. | `True` |

Returns:

| Type | Description | | --- | --- | | `OutputT` | The final output from the graph execution |

Source code in `pydantic_graph/pydantic_graph/beta/graph.py`

```python
async def run(
    self,
    *,
    state: StateT = None,
    deps: DepsT = None,
    inputs: InputT = None,
    span: AbstractContextManager[AbstractSpan] | None = None,
    infer_name: bool = True,
) -> OutputT:
    """Execute the graph and return the final output.

    This is the main entry point for graph execution. It runs the graph
    to completion and returns the final output value.

    Args:
        state: The graph state instance
        deps: The dependencies instance
        inputs: The input data for the graph
        span: Optional span for tracing/instrumentation
        infer_name: Whether to infer the graph name from the calling frame.

    Returns:
        The final output from the graph execution
    """
    if infer_name and self.name is None:
        inferred_name = infer_obj_name(self, depth=2)
        if inferred_name is not None:  # pragma: no branch
            self.name = inferred_name

    async with self.iter(state=state, deps=deps, inputs=inputs, span=span, infer_name=False) as graph_run:
        # Note: This would probably be better using `async for _ in graph_run`, but this tests the `next` method,
        # which I'm less confident will be implemented correctly if not used on the critical path. We can change it
        # once we have tests, etc.
        event: Any = None
        while True:
            try:
                event = await graph_run.next(event)
            except StopAsyncIteration:
                assert isinstance(event, EndMarker), 'Graph run should end with an EndMarker.'
                return cast(EndMarker[OutputT], event).value

```

#### iter

```python
iter(
    *,
    state: StateT = None,
    deps: DepsT = None,
    inputs: InputT = None,
    span: (
        AbstractContextManager[AbstractSpan] | None
    ) = None,
    infer_name: bool = True
) -> AsyncIterator[GraphRun[StateT, DepsT, OutputT]]

```

Create an iterator for step-by-step graph execution.

This method allows for more fine-grained control over graph execution, enabling inspection of intermediate states and results.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `state` | `StateT` | The graph state instance | `None` | | `deps` | `DepsT` | The dependencies instance | `None` | | `inputs` | `InputT` | The input data for the graph | `None` | | `span` | `AbstractContextManager[AbstractSpan] | None` | Optional span for tracing/instrumentation | `None` | | `infer_name` | `bool` | Whether to infer the graph name from the calling frame. | `True` |

Yields:

| Type | Description | | --- | --- | | `AsyncIterator[GraphRun[StateT, DepsT, OutputT]]` | A GraphRun instance that can be iterated for step-by-step execution |

Source code in `pydantic_graph/pydantic_graph/beta/graph.py`

```python
@asynccontextmanager
async def iter(
    self,
    *,
    state: StateT = None,
    deps: DepsT = None,
    inputs: InputT = None,
    span: AbstractContextManager[AbstractSpan] | None = None,
    infer_name: bool = True,
) -> AsyncIterator[GraphRun[StateT, DepsT, OutputT]]:
    """Create an iterator for step-by-step graph execution.

    This method allows for more fine-grained control over graph execution,
    enabling inspection of intermediate states and results.

    Args:
        state: The graph state instance
        deps: The dependencies instance
        inputs: The input data for the graph
        span: Optional span for tracing/instrumentation
        infer_name: Whether to infer the graph name from the calling frame.

    Yields:
        A GraphRun instance that can be iterated for step-by-step execution
    """
    if infer_name and self.name is None:
        inferred_name = infer_obj_name(self, depth=3)  # depth=3 because asynccontextmanager adds one
        if inferred_name is not None:  # pragma: no branch
            self.name = inferred_name

    with ExitStack() as stack:
        entered_span: AbstractSpan | None = None
        if span is None:
            if self.auto_instrument:
                entered_span = stack.enter_context(logfire_span('run graph {graph.name}', graph=self))
        else:
            entered_span = stack.enter_context(span)
        traceparent = None if entered_span is None else get_traceparent(entered_span)
        async with GraphRun[StateT, DepsT, OutputT](
            graph=self,
            state=state,
            deps=deps,
            inputs=inputs,
            traceparent=traceparent,
        ) as graph_run:
            yield graph_run

```

#### render

```python
render(
    *,
    title: str | None = None,
    direction: StateDiagramDirection | None = None
) -> str

```

Render the graph as a Mermaid diagram string.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `title` | `str | None` | Optional title for the diagram | `None` | | `direction` | `StateDiagramDirection | None` | Optional direction for the diagram layout | `None` |

Returns:

| Type | Description | | --- | --- | | `str` | A string containing the Mermaid diagram representation |

Source code in `pydantic_graph/pydantic_graph/beta/graph.py`

```python
def render(self, *, title: str | None = None, direction: StateDiagramDirection | None = None) -> str:
    """Render the graph as a Mermaid diagram string.

    Args:
        title: Optional title for the diagram
        direction: Optional direction for the diagram layout

    Returns:
        A string containing the Mermaid diagram representation
    """
    from pydantic_graph.beta.mermaid import build_mermaid_graph

    return build_mermaid_graph(self.nodes, self.edges_by_source).render(title=title, direction=direction)

```

#### **str**

```python
__str__() -> str

```

Return a Mermaid diagram representation of the graph.

Returns:

| Type | Description | | --- | --- | | `str` | A string containing the Mermaid diagram of the graph |

Source code in `pydantic_graph/pydantic_graph/beta/graph.py`

```python
def __str__(self) -> str:
    """Return a Mermaid diagram representation of the graph.

    Returns:
        A string containing the Mermaid diagram of the graph
    """
    return self.render()

```
