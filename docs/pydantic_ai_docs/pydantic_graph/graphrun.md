### GraphRun

Bases: `Generic[StateT, DepsT, RunEndT]`

A stateful, async-iterable run of a Graph.

You typically get a `GraphRun` instance from calling `async with [my_graph.iter(...)][pydantic_graph.graph.Graph.iter] as graph_run:`. That gives you the ability to iterate through nodes as they run, either by `async for` iteration or by repeatedly calling `.next(...)`.

Here's an example of iterating over the graph from above: iter_never_42.py

```py
from copy import deepcopy
from never_42 import Increment, MyState, never_42_graph

async def main():
    state = MyState(1)
    async with never_42_graph.iter(Increment(), state=state) as graph_run:
        node_states = [(graph_run.next_node, deepcopy(graph_run.state))]
        async for node in graph_run:
            node_states.append((node, deepcopy(graph_run.state)))
        print(node_states)
        '''
        [
            (Increment(), MyState(number=1)),
            (Increment(), MyState(number=1)),
            (Check42(), MyState(number=2)),
            (End(data=2), MyState(number=2)),
        ]
        '''

    state = MyState(41)
    async with never_42_graph.iter(Increment(), state=state) as graph_run:
        node_states = [(graph_run.next_node, deepcopy(graph_run.state))]
        async for node in graph_run:
            node_states.append((node, deepcopy(graph_run.state)))
        print(node_states)
        '''
        [
            (Increment(), MyState(number=41)),
            (Increment(), MyState(number=41)),
            (Check42(), MyState(number=42)),
            (Increment(), MyState(number=42)),
            (Check42(), MyState(number=43)),
            (End(data=43), MyState(number=43)),
        ]
        '''

```

See the GraphRun.next documentation for an example of how to manually drive the graph run.

Source code in `pydantic_graph/pydantic_graph/graph.py`

````python
class GraphRun(Generic[StateT, DepsT, RunEndT]):
    """A stateful, async-iterable run of a [`Graph`][pydantic_graph.graph.Graph].

    You typically get a `GraphRun` instance from calling
    `async with [my_graph.iter(...)][pydantic_graph.graph.Graph.iter] as graph_run:`. That gives you the ability to iterate
    through nodes as they run, either by `async for` iteration or by repeatedly calling `.next(...)`.

    Here's an example of iterating over the graph from [above][pydantic_graph.graph.Graph]:
    ```py {title="iter_never_42.py" noqa="I001" requires="never_42.py"}
    from copy import deepcopy
    from never_42 import Increment, MyState, never_42_graph

    async def main():
        state = MyState(1)
        async with never_42_graph.iter(Increment(), state=state) as graph_run:
            node_states = [(graph_run.next_node, deepcopy(graph_run.state))]
            async for node in graph_run:
                node_states.append((node, deepcopy(graph_run.state)))
            print(node_states)
            '''
            [
                (Increment(), MyState(number=1)),
                (Increment(), MyState(number=1)),
                (Check42(), MyState(number=2)),
                (End(data=2), MyState(number=2)),
            ]
            '''

        state = MyState(41)
        async with never_42_graph.iter(Increment(), state=state) as graph_run:
            node_states = [(graph_run.next_node, deepcopy(graph_run.state))]
            async for node in graph_run:
                node_states.append((node, deepcopy(graph_run.state)))
            print(node_states)
            '''
            [
                (Increment(), MyState(number=41)),
                (Increment(), MyState(number=41)),
                (Check42(), MyState(number=42)),
                (Increment(), MyState(number=42)),
                (Check42(), MyState(number=43)),
                (End(data=43), MyState(number=43)),
            ]
            '''
    ```

    See the [`GraphRun.next` documentation][pydantic_graph.graph.GraphRun.next] for an example of how to manually
    drive the graph run.
    """

    def __init__(
        self,
        *,
        graph: Graph[StateT, DepsT, RunEndT],
        start_node: BaseNode[StateT, DepsT, RunEndT],
        persistence: BaseStatePersistence[StateT, RunEndT],
        state: StateT,
        deps: DepsT,
        traceparent: str | None,
        snapshot_id: str | None = None,
    ):
        """Create a new run for a given graph, starting at the specified node.

        Typically, you'll use [`Graph.iter`][pydantic_graph.graph.Graph.iter] rather than calling this directly.

        Args:
            graph: The [`Graph`][pydantic_graph.graph.Graph] to run.
            start_node: The node where execution will begin.
            persistence: State persistence interface.
            state: A shared state object or primitive (like a counter, dataclass, etc.) that is available
                to all nodes via `ctx.state`.
            deps: Optional dependencies that each node can access via `ctx.deps`, e.g. database connections,
                configuration, or logging clients.
            traceparent: The traceparent for the span used for the graph run.
            snapshot_id: The ID of the snapshot the node came from.
        """
        self.graph = graph
        self.persistence = persistence
        self._snapshot_id: str | None = snapshot_id
        self.state = state
        self.deps = deps

        self.__traceparent = traceparent
        self._next_node: BaseNode[StateT, DepsT, RunEndT] | End[RunEndT] = start_node
        self._is_started: bool = False

    @overload
    def _traceparent(self, *, required: typing_extensions.Literal[False]) -> str | None: ...
    @overload
    def _traceparent(self) -> str: ...
    def _traceparent(self, *, required: bool = True) -> str | None:
        if self.__traceparent is None and required:  # pragma: no cover
            raise exceptions.GraphRuntimeError('No span was created for this graph run')
        return self.__traceparent

    @property
    def next_node(self) -> BaseNode[StateT, DepsT, RunEndT] | End[RunEndT]:
        """The next node that will be run in the graph.

        This is the next node that will be used during async iteration, or if a node is not passed to `self.next(...)`.
        """
        return self._next_node

    @property
    def result(self) -> GraphRunResult[StateT, RunEndT] | None:
        """The final result of the graph run if the run is completed, otherwise `None`."""
        if not isinstance(self._next_node, End):
            return None  # The GraphRun has not finished running
        return GraphRunResult[StateT, RunEndT](
            self._next_node.data,
            state=self.state,
            persistence=self.persistence,
            traceparent=self._traceparent(required=False),
        )

    async def next(
        self, node: BaseNode[StateT, DepsT, RunEndT] | None = None
    ) -> BaseNode[StateT, DepsT, RunEndT] | End[RunEndT]:
        """Manually drive the graph run by passing in the node you want to run next.

        This lets you inspect or mutate the node before continuing execution, or skip certain nodes
        under dynamic conditions. The graph run should stop when you return an [`End`][pydantic_graph.nodes.End] node.

        Here's an example of using `next` to drive the graph from [above][pydantic_graph.graph.Graph]:
        ```py {title="next_never_42.py" noqa="I001" requires="never_42.py"}
        from copy import deepcopy
        from pydantic_graph import End
        from never_42 import Increment, MyState, never_42_graph

        async def main():
            state = MyState(48)
            async with never_42_graph.iter(Increment(), state=state) as graph_run:
                next_node = graph_run.next_node  # start with the first node
                node_states = [(next_node, deepcopy(graph_run.state))]

                while not isinstance(next_node, End):
                    if graph_run.state.number == 50:
                        graph_run.state.number = 42
                    next_node = await graph_run.next(next_node)
                    node_states.append((next_node, deepcopy(graph_run.state)))

                print(node_states)
                '''
                [
                    (Increment(), MyState(number=48)),
                    (Check42(), MyState(number=49)),
                    (End(data=49), MyState(number=49)),
                ]
                '''
        ```

        Args:
            node: The node to run next in the graph. If not specified, uses `self.next_node`, which is initialized to
                the `start_node` of the run and updated each time a new node is returned.

        Returns:
            The next node returned by the graph logic, or an [`End`][pydantic_graph.nodes.End] node if
            the run has completed.
        """
        if node is None:
            # This cast is necessary because self._next_node could be an `End`. You'll get a runtime error if that's
            # the case, but if it is, the only way to get there would be to have tried calling next manually after
            # the run finished. Either way, maybe it would be better to not do this cast...
            node = cast(BaseNode[StateT, DepsT, RunEndT], self._next_node)
            node_snapshot_id = node.get_snapshot_id()
        else:
            node_snapshot_id = node.get_snapshot_id()

        if node_snapshot_id != self._snapshot_id:
            await self.persistence.snapshot_node_if_new(node_snapshot_id, self.state, node)
            self._snapshot_id = node_snapshot_id

        if not isinstance(node, BaseNode):
            # While technically this is not compatible with the documented method signature, it's an easy mistake to
            # make, and we should eagerly provide a more helpful error message than you'd get otherwise.
            raise TypeError(f'`next` must be called with a `BaseNode` instance, got {node!r}.')

        node_id = node.get_node_id()
        if node_id not in self.graph.node_defs:
            raise exceptions.GraphRuntimeError(f'Node `{node}` is not in the graph.')

        with ExitStack() as stack:
            if self.graph.auto_instrument:  # pragma: no branch
                # Separate variable because we actually don't want logfire's f-string magic here,
                # we want the span_name to be preformatted for other backends
                # as requested in https://github.com/pydantic/pydantic-ai/issues/3173.
                span_name = f'run node {node_id}'
                stack.enter_context(logfire_span(span_name, node_id=node_id, node=node))

            async with self.persistence.record_run(node_snapshot_id):
                ctx = GraphRunContext(state=self.state, deps=self.deps)
                self._next_node = await node.run(ctx)

        if isinstance(self._next_node, End):
            self._snapshot_id = self._next_node.get_snapshot_id()
            await self.persistence.snapshot_end(self.state, self._next_node)
        elif isinstance(self._next_node, BaseNode):
            self._snapshot_id = self._next_node.get_snapshot_id()
            await self.persistence.snapshot_node(self.state, self._next_node)
        else:
            raise exceptions.GraphRuntimeError(
                f'Invalid node return type: `{type(self._next_node).__name__}`. Expected `BaseNode` or `End`.'
            )

        return self._next_node

    def __aiter__(self) -> AsyncIterator[BaseNode[StateT, DepsT, RunEndT] | End[RunEndT]]:
        return self

    async def __anext__(self) -> BaseNode[StateT, DepsT, RunEndT] | End[RunEndT]:
        """Use the last returned node as the input to `Graph.next`."""
        if not self._is_started:
            self._is_started = True
            return self._next_node

        if isinstance(self._next_node, End):
            raise StopAsyncIteration

        return await self.next(self._next_node)

    def __repr__(self) -> str:
        return f'<GraphRun graph={self.graph.name or "[unnamed]"}>'

````

#### **init**

```python
__init__(
    *,
    graph: Graph[StateT, DepsT, RunEndT],
    start_node: BaseNode[StateT, DepsT, RunEndT],
    persistence: BaseStatePersistence[StateT, RunEndT],
    state: StateT,
    deps: DepsT,
    traceparent: str | None,
    snapshot_id: str | None = None
)

```

Create a new run for a given graph, starting at the specified node.

Typically, you'll use Graph.iter rather than calling this directly.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `graph` | `Graph[StateT, DepsT, RunEndT]` | The Graph to run. | _required_ | | `start_node` | `BaseNode[StateT, DepsT, RunEndT]` | The node where execution will begin. | _required_ | | `persistence` | `BaseStatePersistence[StateT, RunEndT]` | State persistence interface. | _required_ | | `state` | `StateT` | A shared state object or primitive (like a counter, dataclass, etc.) that is available to all nodes via ctx.state. | _required_ | | `deps` | `DepsT` | Optional dependencies that each node can access via ctx.deps, e.g. database connections, configuration, or logging clients. | _required_ | | `traceparent` | `str | None` | The traceparent for the span used for the graph run. | _required_ | | `snapshot_id` | `str | None` | The ID of the snapshot the node came from. | `None` |

Source code in `pydantic_graph/pydantic_graph/graph.py`

```python
def __init__(
    self,
    *,
    graph: Graph[StateT, DepsT, RunEndT],
    start_node: BaseNode[StateT, DepsT, RunEndT],
    persistence: BaseStatePersistence[StateT, RunEndT],
    state: StateT,
    deps: DepsT,
    traceparent: str | None,
    snapshot_id: str | None = None,
):
    """Create a new run for a given graph, starting at the specified node.

    Typically, you'll use [`Graph.iter`][pydantic_graph.graph.Graph.iter] rather than calling this directly.

    Args:
        graph: The [`Graph`][pydantic_graph.graph.Graph] to run.
        start_node: The node where execution will begin.
        persistence: State persistence interface.
        state: A shared state object or primitive (like a counter, dataclass, etc.) that is available
            to all nodes via `ctx.state`.
        deps: Optional dependencies that each node can access via `ctx.deps`, e.g. database connections,
            configuration, or logging clients.
        traceparent: The traceparent for the span used for the graph run.
        snapshot_id: The ID of the snapshot the node came from.
    """
    self.graph = graph
    self.persistence = persistence
    self._snapshot_id: str | None = snapshot_id
    self.state = state
    self.deps = deps

    self.__traceparent = traceparent
    self._next_node: BaseNode[StateT, DepsT, RunEndT] | End[RunEndT] = start_node
    self._is_started: bool = False

```

#### next_node

```python
next_node: BaseNode[StateT, DepsT, RunEndT] | End[RunEndT]

```

The next node that will be run in the graph.

This is the next node that will be used during async iteration, or if a node is not passed to `self.next(...)`.

#### result

```python
result: GraphRunResult[StateT, RunEndT] | None

```

The final result of the graph run if the run is completed, otherwise `None`.

#### next

```python
next(
    node: BaseNode[StateT, DepsT, RunEndT] | None = None,
) -> BaseNode[StateT, DepsT, RunEndT] | End[RunEndT]

```

Manually drive the graph run by passing in the node you want to run next.

This lets you inspect or mutate the node before continuing execution, or skip certain nodes under dynamic conditions. The graph run should stop when you return an End node.

Here's an example of using `next` to drive the graph from above: next_never_42.py

```py
from copy import deepcopy
from pydantic_graph import End
from never_42 import Increment, MyState, never_42_graph

async def main():
    state = MyState(48)
    async with never_42_graph.iter(Increment(), state=state) as graph_run:
        next_node = graph_run.next_node  # start with the first node
        node_states = [(next_node, deepcopy(graph_run.state))]

        while not isinstance(next_node, End):
            if graph_run.state.number == 50:
                graph_run.state.number = 42
            next_node = await graph_run.next(next_node)
            node_states.append((next_node, deepcopy(graph_run.state)))

        print(node_states)
        '''
        [
            (Increment(), MyState(number=48)),
            (Check42(), MyState(number=49)),
            (End(data=49), MyState(number=49)),
        ]
        '''

```

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `node` | `BaseNode[StateT, DepsT, RunEndT] | None` | The node to run next in the graph. If not specified, uses self.next_node, which is initialized to the start_node of the run and updated each time a new node is returned. | `None` |

Returns:

| Type | Description | | --- | --- | | `BaseNode[StateT, DepsT, RunEndT] | End[RunEndT]` | The next node returned by the graph logic, or an End node if | | `BaseNode[StateT, DepsT, RunEndT] | End[RunEndT]` | the run has completed. |

Source code in `pydantic_graph/pydantic_graph/graph.py`

````python
async def next(
    self, node: BaseNode[StateT, DepsT, RunEndT] | None = None
) -> BaseNode[StateT, DepsT, RunEndT] | End[RunEndT]:
    """Manually drive the graph run by passing in the node you want to run next.

    This lets you inspect or mutate the node before continuing execution, or skip certain nodes
    under dynamic conditions. The graph run should stop when you return an [`End`][pydantic_graph.nodes.End] node.

    Here's an example of using `next` to drive the graph from [above][pydantic_graph.graph.Graph]:
    ```py {title="next_never_42.py" noqa="I001" requires="never_42.py"}
    from copy import deepcopy
    from pydantic_graph import End
    from never_42 import Increment, MyState, never_42_graph

    async def main():
        state = MyState(48)
        async with never_42_graph.iter(Increment(), state=state) as graph_run:
            next_node = graph_run.next_node  # start with the first node
            node_states = [(next_node, deepcopy(graph_run.state))]

            while not isinstance(next_node, End):
                if graph_run.state.number == 50:
                    graph_run.state.number = 42
                next_node = await graph_run.next(next_node)
                node_states.append((next_node, deepcopy(graph_run.state)))

            print(node_states)
            '''
            [
                (Increment(), MyState(number=48)),
                (Check42(), MyState(number=49)),
                (End(data=49), MyState(number=49)),
            ]
            '''
    ```

    Args:
        node: The node to run next in the graph. If not specified, uses `self.next_node`, which is initialized to
            the `start_node` of the run and updated each time a new node is returned.

    Returns:
        The next node returned by the graph logic, or an [`End`][pydantic_graph.nodes.End] node if
        the run has completed.
    """
    if node is None:
        # This cast is necessary because self._next_node could be an `End`. You'll get a runtime error if that's
        # the case, but if it is, the only way to get there would be to have tried calling next manually after
        # the run finished. Either way, maybe it would be better to not do this cast...
        node = cast(BaseNode[StateT, DepsT, RunEndT], self._next_node)
        node_snapshot_id = node.get_snapshot_id()
    else:
        node_snapshot_id = node.get_snapshot_id()

    if node_snapshot_id != self._snapshot_id:
        await self.persistence.snapshot_node_if_new(node_snapshot_id, self.state, node)
        self._snapshot_id = node_snapshot_id

    if not isinstance(node, BaseNode):
        # While technically this is not compatible with the documented method signature, it's an easy mistake to
        # make, and we should eagerly provide a more helpful error message than you'd get otherwise.
        raise TypeError(f'`next` must be called with a `BaseNode` instance, got {node!r}.')

    node_id = node.get_node_id()
    if node_id not in self.graph.node_defs:
        raise exceptions.GraphRuntimeError(f'Node `{node}` is not in the graph.')

    with ExitStack() as stack:
        if self.graph.auto_instrument:  # pragma: no branch
            # Separate variable because we actually don't want logfire's f-string magic here,
            # we want the span_name to be preformatted for other backends
            # as requested in https://github.com/pydantic/pydantic-ai/issues/3173.
            span_name = f'run node {node_id}'
            stack.enter_context(logfire_span(span_name, node_id=node_id, node=node))

        async with self.persistence.record_run(node_snapshot_id):
            ctx = GraphRunContext(state=self.state, deps=self.deps)
            self._next_node = await node.run(ctx)

    if isinstance(self._next_node, End):
        self._snapshot_id = self._next_node.get_snapshot_id()
        await self.persistence.snapshot_end(self.state, self._next_node)
    elif isinstance(self._next_node, BaseNode):
        self._snapshot_id = self._next_node.get_snapshot_id()
        await self.persistence.snapshot_node(self.state, self._next_node)
    else:
        raise exceptions.GraphRuntimeError(
            f'Invalid node return type: `{type(self._next_node).__name__}`. Expected `BaseNode` or `End`.'
        )

    return self._next_node

````

#### **anext**

```python
__anext__() -> (
    BaseNode[StateT, DepsT, RunEndT] | End[RunEndT]
)

```

Use the last returned node as the input to `Graph.next`.

Source code in `pydantic_graph/pydantic_graph/graph.py`

```python
async def __anext__(self) -> BaseNode[StateT, DepsT, RunEndT] | End[RunEndT]:
    """Use the last returned node as the input to `Graph.next`."""
    if not self._is_started:
        self._is_started = True
        return self._next_node

    if isinstance(self._next_node, End):
        raise StopAsyncIteration

    return await self.next(self._next_node)

```
