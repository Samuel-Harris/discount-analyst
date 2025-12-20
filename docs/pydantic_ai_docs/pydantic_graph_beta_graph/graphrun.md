### GraphRun

Bases: `Generic[StateT, DepsT, OutputT]`

A single execution instance of a graph.

GraphRun manages the execution state for a single run of a graph, including task scheduling, fork/join coordination, and result tracking.

Type Parameters

StateT: The type of the graph state DepsT: The type of the dependencies OutputT: The type of the output data

Source code in `pydantic_graph/pydantic_graph/beta/graph.py`

```python
class GraphRun(Generic[StateT, DepsT, OutputT]):
    """A single execution instance of a graph.

    GraphRun manages the execution state for a single run of a graph,
    including task scheduling, fork/join coordination, and result tracking.

    Type Parameters:
        StateT: The type of the graph state
        DepsT: The type of the dependencies
        OutputT: The type of the output data
    """

    def __init__(
        self,
        graph: Graph[StateT, DepsT, InputT, OutputT],
        *,
        state: StateT,
        deps: DepsT,
        inputs: InputT,
        traceparent: str | None,
    ):
        """Initialize a graph run.

        Args:
            graph: The graph to execute
            state: The graph state instance
            deps: The dependencies instance
            inputs: The input data for the graph
            traceparent: Optional trace parent for instrumentation
        """
        self.graph = graph
        """The graph being executed."""

        self.state = state
        """The graph state instance."""

        self.deps = deps
        """The dependencies instance."""

        self.inputs = inputs
        """The initial input data."""

        self._active_reducers: dict[tuple[JoinID, NodeRunID], JoinState] = {}
        """Active reducers for join operations."""

        self._next: EndMarker[OutputT] | Sequence[GraphTask] | None = None
        """The next item to be processed."""

        self._next_task_id = 0
        self._next_node_run_id = 0
        initial_fork_stack: ForkStack = (ForkStackItem(StartNode.id, self._get_next_node_run_id(), 0),)
        self._first_task = GraphTask(
            node_id=StartNode.id, inputs=inputs, fork_stack=initial_fork_stack, task_id=self._get_next_task_id()
        )
        self._iterator_task_group = create_task_group()
        self._iterator_instance = _GraphIterator[StateT, DepsT, OutputT](
            self.graph,
            self.state,
            self.deps,
            self._iterator_task_group,
            self._get_next_node_run_id,
            self._get_next_task_id,
        )
        self._iterator = self._iterator_instance.iter_graph(self._first_task)

        self.__traceparent = traceparent
        self._async_exit_stack = AsyncExitStack()

    async def __aenter__(self):
        self._async_exit_stack.enter_context(_unwrap_exception_groups())
        await self._async_exit_stack.enter_async_context(self._iterator_task_group)
        await self._async_exit_stack.enter_async_context(self._iterator_context())
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any):
        await self._async_exit_stack.__aexit__(exc_type, exc_val, exc_tb)

    @asynccontextmanager
    async def _iterator_context(self):
        try:
            yield
        finally:
            self._iterator_instance.iter_stream_sender.close()
            self._iterator_instance.iter_stream_receiver.close()
            await self._iterator.aclose()

    @overload
    def _traceparent(self, *, required: Literal[False]) -> str | None: ...
    @overload
    def _traceparent(self) -> str: ...
    def _traceparent(self, *, required: bool = True) -> str | None:
        """Get the trace parent for instrumentation.

        Args:
            required: Whether to raise an error if no traceparent exists

        Returns:
            The traceparent string, or None if not required and not set

        Raises:
            GraphRuntimeError: If required is True and no traceparent exists
        """
        if self.__traceparent is None and required:  # pragma: no cover
            raise exceptions.GraphRuntimeError('No span was created for this graph run')
        return self.__traceparent

    def __aiter__(self) -> AsyncIterator[EndMarker[OutputT] | Sequence[GraphTask]]:
        """Return self as an async iterator.

        Returns:
            Self for async iteration
        """
        return self

    async def __anext__(self) -> EndMarker[OutputT] | Sequence[GraphTask]:
        """Get the next item in the async iteration.

        Returns:
            The next execution result from the graph
        """
        if self._next is None:
            self._next = await anext(self._iterator)
        else:
            self._next = await self._iterator.asend(self._next)
        return self._next

    async def next(
        self, value: EndMarker[OutputT] | Sequence[GraphTaskRequest] | None = None
    ) -> EndMarker[OutputT] | Sequence[GraphTask]:
        """Advance the graph execution by one step.

        This method allows for sending a value to the iterator, which is useful
        for resuming iteration or overriding intermediate results.

        Args:
            value: Optional value to send to the iterator

        Returns:
            The next execution result: either an EndMarker, or sequence of GraphTasks
        """
        if self._next is None:
            # Prevent `TypeError: can't send non-None value to a just-started async generator`
            # if `next` is called before the `first_node` has run.
            await anext(self)
        if value is not None:
            if isinstance(value, EndMarker):
                self._next = value
            else:
                self._next = [GraphTask.from_request(gtr, self._get_next_task_id) for gtr in value]
        return await anext(self)

    @property
    def next_task(self) -> EndMarker[OutputT] | Sequence[GraphTask]:
        """Get the next task(s) to be executed.

        Returns:
            The next execution item, or the initial task if none is set
        """
        return self._next or [self._first_task]

    @property
    def output(self) -> OutputT | None:
        """Get the final output if the graph has completed.

        Returns:
            The output value if execution is complete, None otherwise
        """
        if isinstance(self._next, EndMarker):
            return self._next.value
        return None

    def _get_next_task_id(self) -> TaskID:
        next_id = TaskID(f'task:{self._next_task_id}')
        self._next_task_id += 1
        return next_id

    def _get_next_node_run_id(self) -> NodeRunID:
        next_id = NodeRunID(f'task:{self._next_node_run_id}')
        self._next_node_run_id += 1
        return next_id

```

#### **init**

```python
__init__(
    graph: Graph[StateT, DepsT, InputT, OutputT],
    *,
    state: StateT,
    deps: DepsT,
    inputs: InputT,
    traceparent: str | None
)

```

Initialize a graph run.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `graph` | `Graph[StateT, DepsT, InputT, OutputT]` | The graph to execute | _required_ | | `state` | `StateT` | The graph state instance | _required_ | | `deps` | `DepsT` | The dependencies instance | _required_ | | `inputs` | `InputT` | The input data for the graph | _required_ | | `traceparent` | `str | None` | Optional trace parent for instrumentation | _required_ |

Source code in `pydantic_graph/pydantic_graph/beta/graph.py`

```python
def __init__(
    self,
    graph: Graph[StateT, DepsT, InputT, OutputT],
    *,
    state: StateT,
    deps: DepsT,
    inputs: InputT,
    traceparent: str | None,
):
    """Initialize a graph run.

    Args:
        graph: The graph to execute
        state: The graph state instance
        deps: The dependencies instance
        inputs: The input data for the graph
        traceparent: Optional trace parent for instrumentation
    """
    self.graph = graph
    """The graph being executed."""

    self.state = state
    """The graph state instance."""

    self.deps = deps
    """The dependencies instance."""

    self.inputs = inputs
    """The initial input data."""

    self._active_reducers: dict[tuple[JoinID, NodeRunID], JoinState] = {}
    """Active reducers for join operations."""

    self._next: EndMarker[OutputT] | Sequence[GraphTask] | None = None
    """The next item to be processed."""

    self._next_task_id = 0
    self._next_node_run_id = 0
    initial_fork_stack: ForkStack = (ForkStackItem(StartNode.id, self._get_next_node_run_id(), 0),)
    self._first_task = GraphTask(
        node_id=StartNode.id, inputs=inputs, fork_stack=initial_fork_stack, task_id=self._get_next_task_id()
    )
    self._iterator_task_group = create_task_group()
    self._iterator_instance = _GraphIterator[StateT, DepsT, OutputT](
        self.graph,
        self.state,
        self.deps,
        self._iterator_task_group,
        self._get_next_node_run_id,
        self._get_next_task_id,
    )
    self._iterator = self._iterator_instance.iter_graph(self._first_task)

    self.__traceparent = traceparent
    self._async_exit_stack = AsyncExitStack()

```

#### graph

```python
graph = graph

```

The graph being executed.

#### state

```python
state = state

```

The graph state instance.

#### deps

```python
deps = deps

```

The dependencies instance.

#### inputs

```python
inputs = inputs

```

The initial input data.

#### **aiter**

```python
__aiter__() -> (
    AsyncIterator[EndMarker[OutputT] | Sequence[GraphTask]]
)

```

Return self as an async iterator.

Returns:

| Type | Description | | --- | --- | | `AsyncIterator[EndMarker[OutputT] | Sequence[GraphTask]]` | Self for async iteration |

Source code in `pydantic_graph/pydantic_graph/beta/graph.py`

```python
def __aiter__(self) -> AsyncIterator[EndMarker[OutputT] | Sequence[GraphTask]]:
    """Return self as an async iterator.

    Returns:
        Self for async iteration
    """
    return self

```

#### **anext**

```python
__anext__() -> EndMarker[OutputT] | Sequence[GraphTask]

```

Get the next item in the async iteration.

Returns:

| Type | Description | | --- | --- | | `EndMarker[OutputT] | Sequence[GraphTask]` | The next execution result from the graph |

Source code in `pydantic_graph/pydantic_graph/beta/graph.py`

```python
async def __anext__(self) -> EndMarker[OutputT] | Sequence[GraphTask]:
    """Get the next item in the async iteration.

    Returns:
        The next execution result from the graph
    """
    if self._next is None:
        self._next = await anext(self._iterator)
    else:
        self._next = await self._iterator.asend(self._next)
    return self._next

```

#### next

```python
next(
    value: (
        EndMarker[OutputT]
        | Sequence[GraphTaskRequest]
        | None
    ) = None,
) -> EndMarker[OutputT] | Sequence[GraphTask]

```

Advance the graph execution by one step.

This method allows for sending a value to the iterator, which is useful for resuming iteration or overriding intermediate results.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `value` | `EndMarker[OutputT] | Sequence[GraphTaskRequest] | None` | Optional value to send to the iterator | `None` |

Returns:

| Type | Description | | --- | --- | | `EndMarker[OutputT] | Sequence[GraphTask]` | The next execution result: either an EndMarker, or sequence of GraphTasks |

Source code in `pydantic_graph/pydantic_graph/beta/graph.py`

```python
async def next(
    self, value: EndMarker[OutputT] | Sequence[GraphTaskRequest] | None = None
) -> EndMarker[OutputT] | Sequence[GraphTask]:
    """Advance the graph execution by one step.

    This method allows for sending a value to the iterator, which is useful
    for resuming iteration or overriding intermediate results.

    Args:
        value: Optional value to send to the iterator

    Returns:
        The next execution result: either an EndMarker, or sequence of GraphTasks
    """
    if self._next is None:
        # Prevent `TypeError: can't send non-None value to a just-started async generator`
        # if `next` is called before the `first_node` has run.
        await anext(self)
    if value is not None:
        if isinstance(value, EndMarker):
            self._next = value
        else:
            self._next = [GraphTask.from_request(gtr, self._get_next_task_id) for gtr in value]
    return await anext(self)

```

#### next_task

```python
next_task: EndMarker[OutputT] | Sequence[GraphTask]

```

Get the next task(s) to be executed.

Returns:

| Type | Description | | --- | --- | | `EndMarker[OutputT] | Sequence[GraphTask]` | The next execution item, or the initial task if none is set |

#### output

```python
output: OutputT | None

```

Get the final output if the graph has completed.

Returns:

| Type | Description | | --- | --- | | `OutputT | None` | The output value if execution is complete, None otherwise |
