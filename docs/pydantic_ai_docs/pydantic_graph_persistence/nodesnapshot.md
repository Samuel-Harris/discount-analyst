### NodeSnapshot

Bases: `Generic[StateT, RunEndT]`

History step describing the execution of a node in a graph.

Source code in `pydantic_graph/pydantic_graph/persistence/__init__.py`

```python
@dataclass(kw_only=True)
class NodeSnapshot(Generic[StateT, RunEndT]):
    """History step describing the execution of a node in a graph."""

    state: StateT
    """The state of the graph before the node is run."""
    node: Annotated[BaseNode[StateT, Any, RunEndT], _utils.CustomNodeSchema()]
    """The node to run next."""
    start_ts: datetime | None = None
    """The timestamp when the node started running, `None` until the run starts."""
    duration: float | None = None
    """The duration of the node run in seconds, if the node has been run."""
    status: SnapshotStatus = 'created'
    """The status of the snapshot."""
    kind: Literal['node'] = 'node'
    """The kind of history step, can be used as a discriminator when deserializing history."""

    id: str = UNSET_SNAPSHOT_ID
    """Unique ID of the snapshot."""

    def __post_init__(self) -> None:
        if self.id == UNSET_SNAPSHOT_ID:
            self.id = self.node.get_snapshot_id()

```

#### state

```python
state: StateT

```

The state of the graph before the node is run.

#### node

```python
node: Annotated[
    BaseNode[StateT, Any, RunEndT], CustomNodeSchema()
]

```

The node to run next.

#### start_ts

```python
start_ts: datetime | None = None

```

The timestamp when the node started running, `None` until the run starts.

#### duration

```python
duration: float | None = None

```

The duration of the node run in seconds, if the node has been run.

#### status

```python
status: SnapshotStatus = 'created'

```

The status of the snapshot.

#### kind

```python
kind: Literal['node'] = 'node'

```

The kind of history step, can be used as a discriminator when deserializing history.

#### id

```python
id: str = UNSET_SNAPSHOT_ID

```

Unique ID of the snapshot.
