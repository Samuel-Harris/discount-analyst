### BaseStatePersistence

Bases: `ABC`, `Generic[StateT, RunEndT]`

Abstract base class for storing the state of a graph run.

Each instance of a `BaseStatePersistence` subclass should be used for a single graph run.

Source code in `pydantic_graph/pydantic_graph/persistence/__init__.py`

```python
class BaseStatePersistence(ABC, Generic[StateT, RunEndT]):
    """Abstract base class for storing the state of a graph run.

    Each instance of a `BaseStatePersistence` subclass should be used for a single graph run.
    """

    @abstractmethod
    async def snapshot_node(self, state: StateT, next_node: BaseNode[StateT, Any, RunEndT]) -> None:
        """Snapshot the state of a graph, when the next step is to run a node.

        This method should add a [`NodeSnapshot`][pydantic_graph.persistence.NodeSnapshot] to persistence.

        Args:
            state: The state of the graph.
            next_node: The next node to run.
        """
        raise NotImplementedError

    @abstractmethod
    async def snapshot_node_if_new(
        self, snapshot_id: str, state: StateT, next_node: BaseNode[StateT, Any, RunEndT]
    ) -> None:
        """Snapshot the state of a graph if the snapshot ID doesn't already exist in persistence.

        This method will generally call [`snapshot_node`][pydantic_graph.persistence.BaseStatePersistence.snapshot_node]
        but should do so in an atomic way.

        Args:
            snapshot_id: The ID of the snapshot to check.
            state: The state of the graph.
            next_node: The next node to run.
        """
        raise NotImplementedError

    @abstractmethod
    async def snapshot_end(self, state: StateT, end: End[RunEndT]) -> None:
        """Snapshot the state of a graph when the graph has ended.

        This method should add an [`EndSnapshot`][pydantic_graph.persistence.EndSnapshot] to persistence.

        Args:
            state: The state of the graph.
            end: data from the end of the run.
        """
        raise NotImplementedError

    @abstractmethod
    def record_run(self, snapshot_id: str) -> AbstractAsyncContextManager[None]:
        """Record the run of the node, or error if the node is already running.

        Args:
            snapshot_id: The ID of the snapshot to record.

        Raises:
            GraphNodeRunningError: if the node status it not `'created'` or `'pending'`.
            LookupError: if the snapshot ID is not found in persistence.

        Returns:
            An async context manager that records the run of the node.

        In particular this should set:

        - [`NodeSnapshot.status`][pydantic_graph.persistence.NodeSnapshot.status] to `'running'` and
          [`NodeSnapshot.start_ts`][pydantic_graph.persistence.NodeSnapshot.start_ts] when the run starts.
        - [`NodeSnapshot.status`][pydantic_graph.persistence.NodeSnapshot.status] to `'success'` or `'error'` and
          [`NodeSnapshot.duration`][pydantic_graph.persistence.NodeSnapshot.duration] when the run finishes.
        """
        raise NotImplementedError

    @abstractmethod
    async def load_next(self) -> NodeSnapshot[StateT, RunEndT] | None:
        """Retrieve a node snapshot with status `'created`' and set its status to `'pending'`.

        This is used by [`Graph.iter_from_persistence`][pydantic_graph.graph.Graph.iter_from_persistence]
        to get the next node to run.

        Returns: The snapshot, or `None` if no snapshot with status `'created`' exists.
        """
        raise NotImplementedError

    @abstractmethod
    async def load_all(self) -> list[Snapshot[StateT, RunEndT]]:
        """Load the entire history of snapshots.

        `load_all` is not used by pydantic-graph itself, instead it's provided to make it convenient to
        get all [snapshots][pydantic_graph.persistence.Snapshot] from persistence.

        Returns: The list of snapshots.
        """
        raise NotImplementedError

    def set_graph_types(self, graph: Graph[StateT, Any, RunEndT]) -> None:
        """Set the types of the state and run end from a graph.

        You generally won't need to customise this method, instead implement
        [`set_types`][pydantic_graph.persistence.BaseStatePersistence.set_types] and
        [`should_set_types`][pydantic_graph.persistence.BaseStatePersistence.should_set_types].
        """
        if self.should_set_types():
            with _utils.set_nodes_type_context(graph.get_nodes()):
                self.set_types(*graph.inferred_types)

    def should_set_types(self) -> bool:
        """Whether types need to be set.

        Implementations should override this method to return `True` when types have not been set if they are needed.
        """
        return False

    def set_types(self, state_type: type[StateT], run_end_type: type[RunEndT]) -> None:
        """Set the types of the state and run end.

        This can be used to create [type adapters][pydantic.TypeAdapter] for serializing and deserializing snapshots,
        e.g. with [`build_snapshot_list_type_adapter`][pydantic_graph.persistence.build_snapshot_list_type_adapter].

        Args:
            state_type: The state type.
            run_end_type: The run end type.
        """
        pass

```

#### snapshot_node

```python
snapshot_node(
    state: StateT, next_node: BaseNode[StateT, Any, RunEndT]
) -> None

```

Snapshot the state of a graph, when the next step is to run a node.

This method should add a NodeSnapshot to persistence.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `state` | `StateT` | The state of the graph. | _required_ | | `next_node` | `BaseNode[StateT, Any, RunEndT]` | The next node to run. | _required_ |

Source code in `pydantic_graph/pydantic_graph/persistence/__init__.py`

```python
@abstractmethod
async def snapshot_node(self, state: StateT, next_node: BaseNode[StateT, Any, RunEndT]) -> None:
    """Snapshot the state of a graph, when the next step is to run a node.

    This method should add a [`NodeSnapshot`][pydantic_graph.persistence.NodeSnapshot] to persistence.

    Args:
        state: The state of the graph.
        next_node: The next node to run.
    """
    raise NotImplementedError

```

#### snapshot_node_if_new

```python
snapshot_node_if_new(
    snapshot_id: str,
    state: StateT,
    next_node: BaseNode[StateT, Any, RunEndT],
) -> None

```

Snapshot the state of a graph if the snapshot ID doesn't already exist in persistence.

This method will generally call snapshot_node but should do so in an atomic way.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `snapshot_id` | `str` | The ID of the snapshot to check. | _required_ | | `state` | `StateT` | The state of the graph. | _required_ | | `next_node` | `BaseNode[StateT, Any, RunEndT]` | The next node to run. | _required_ |

Source code in `pydantic_graph/pydantic_graph/persistence/__init__.py`

```python
@abstractmethod
async def snapshot_node_if_new(
    self, snapshot_id: str, state: StateT, next_node: BaseNode[StateT, Any, RunEndT]
) -> None:
    """Snapshot the state of a graph if the snapshot ID doesn't already exist in persistence.

    This method will generally call [`snapshot_node`][pydantic_graph.persistence.BaseStatePersistence.snapshot_node]
    but should do so in an atomic way.

    Args:
        snapshot_id: The ID of the snapshot to check.
        state: The state of the graph.
        next_node: The next node to run.
    """
    raise NotImplementedError

```

#### snapshot_end

```python
snapshot_end(state: StateT, end: End[RunEndT]) -> None

```

Snapshot the state of a graph when the graph has ended.

This method should add an EndSnapshot to persistence.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `state` | `StateT` | The state of the graph. | _required_ | | `end` | `End[RunEndT]` | data from the end of the run. | _required_ |

Source code in `pydantic_graph/pydantic_graph/persistence/__init__.py`

```python
@abstractmethod
async def snapshot_end(self, state: StateT, end: End[RunEndT]) -> None:
    """Snapshot the state of a graph when the graph has ended.

    This method should add an [`EndSnapshot`][pydantic_graph.persistence.EndSnapshot] to persistence.

    Args:
        state: The state of the graph.
        end: data from the end of the run.
    """
    raise NotImplementedError

```

#### record_run

```python
record_run(
    snapshot_id: str,
) -> AbstractAsyncContextManager[None]

```

Record the run of the node, or error if the node is already running.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `snapshot_id` | `str` | The ID of the snapshot to record. | _required_ |

Raises:

| Type | Description | | --- | --- | | `GraphNodeRunningError` | if the node status it not 'created' or 'pending'. | | `LookupError` | if the snapshot ID is not found in persistence. |

Returns:

| Type | Description | | --- | --- | | `AbstractAsyncContextManager[None]` | An async context manager that records the run of the node. |

In particular this should set:

- NodeSnapshot.status to `'running'` and NodeSnapshot.start_ts when the run starts.
- NodeSnapshot.status to `'success'` or `'error'` and NodeSnapshot.duration when the run finishes.

Source code in `pydantic_graph/pydantic_graph/persistence/__init__.py`

```python
@abstractmethod
def record_run(self, snapshot_id: str) -> AbstractAsyncContextManager[None]:
    """Record the run of the node, or error if the node is already running.

    Args:
        snapshot_id: The ID of the snapshot to record.

    Raises:
        GraphNodeRunningError: if the node status it not `'created'` or `'pending'`.
        LookupError: if the snapshot ID is not found in persistence.

    Returns:
        An async context manager that records the run of the node.

    In particular this should set:

    - [`NodeSnapshot.status`][pydantic_graph.persistence.NodeSnapshot.status] to `'running'` and
      [`NodeSnapshot.start_ts`][pydantic_graph.persistence.NodeSnapshot.start_ts] when the run starts.
    - [`NodeSnapshot.status`][pydantic_graph.persistence.NodeSnapshot.status] to `'success'` or `'error'` and
      [`NodeSnapshot.duration`][pydantic_graph.persistence.NodeSnapshot.duration] when the run finishes.
    """
    raise NotImplementedError

```

#### load_next

```python
load_next() -> NodeSnapshot[StateT, RunEndT] | None

```

Retrieve a node snapshot with status `'created`' and set its status to `'pending'`.

This is used by Graph.iter_from_persistence to get the next node to run.

Returns: The snapshot, or `None` if no snapshot with status `'created`' exists.

Source code in `pydantic_graph/pydantic_graph/persistence/__init__.py`

```python
@abstractmethod
async def load_next(self) -> NodeSnapshot[StateT, RunEndT] | None:
    """Retrieve a node snapshot with status `'created`' and set its status to `'pending'`.

    This is used by [`Graph.iter_from_persistence`][pydantic_graph.graph.Graph.iter_from_persistence]
    to get the next node to run.

    Returns: The snapshot, or `None` if no snapshot with status `'created`' exists.
    """
    raise NotImplementedError

```

#### load_all

```python
load_all() -> list[Snapshot[StateT, RunEndT]]

```

Load the entire history of snapshots.

`load_all` is not used by pydantic-graph itself, instead it's provided to make it convenient to get all snapshots from persistence.

Returns: The list of snapshots.

Source code in `pydantic_graph/pydantic_graph/persistence/__init__.py`

```python
@abstractmethod
async def load_all(self) -> list[Snapshot[StateT, RunEndT]]:
    """Load the entire history of snapshots.

    `load_all` is not used by pydantic-graph itself, instead it's provided to make it convenient to
    get all [snapshots][pydantic_graph.persistence.Snapshot] from persistence.

    Returns: The list of snapshots.
    """
    raise NotImplementedError

```

#### set_graph_types

```python
set_graph_types(graph: Graph[StateT, Any, RunEndT]) -> None

```

Set the types of the state and run end from a graph.

You generally won't need to customise this method, instead implement set_types and should_set_types.

Source code in `pydantic_graph/pydantic_graph/persistence/__init__.py`

```python
def set_graph_types(self, graph: Graph[StateT, Any, RunEndT]) -> None:
    """Set the types of the state and run end from a graph.

    You generally won't need to customise this method, instead implement
    [`set_types`][pydantic_graph.persistence.BaseStatePersistence.set_types] and
    [`should_set_types`][pydantic_graph.persistence.BaseStatePersistence.should_set_types].
    """
    if self.should_set_types():
        with _utils.set_nodes_type_context(graph.get_nodes()):
            self.set_types(*graph.inferred_types)

```

#### should_set_types

```python
should_set_types() -> bool

```

Whether types need to be set.

Implementations should override this method to return `True` when types have not been set if they are needed.

Source code in `pydantic_graph/pydantic_graph/persistence/__init__.py`

```python
def should_set_types(self) -> bool:
    """Whether types need to be set.

    Implementations should override this method to return `True` when types have not been set if they are needed.
    """
    return False

```

#### set_types

```python
set_types(
    state_type: type[StateT], run_end_type: type[RunEndT]
) -> None

```

Set the types of the state and run end.

This can be used to create type adapters for serializing and deserializing snapshots, e.g. with build_snapshot_list_type_adapter.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `state_type` | `type[StateT]` | The state type. | _required_ | | `run_end_type` | `type[RunEndT]` | The run end type. | _required_ |

Source code in `pydantic_graph/pydantic_graph/persistence/__init__.py`

```python
def set_types(self, state_type: type[StateT], run_end_type: type[RunEndT]) -> None:
    """Set the types of the state and run end.

    This can be used to create [type adapters][pydantic.TypeAdapter] for serializing and deserializing snapshots,
    e.g. with [`build_snapshot_list_type_adapter`][pydantic_graph.persistence.build_snapshot_list_type_adapter].

    Args:
        state_type: The state type.
        run_end_type: The run end type.
    """
    pass

```
