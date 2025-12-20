### EndSnapshot

Bases: `Generic[StateT, RunEndT]`

History step describing the end of a graph run.

Source code in `pydantic_graph/pydantic_graph/persistence/__init__.py`

```python
@dataclass(kw_only=True)
class EndSnapshot(Generic[StateT, RunEndT]):
    """History step describing the end of a graph run."""

    state: StateT
    """The state of the graph at the end of the run."""
    result: End[RunEndT]
    """The result of the graph run."""
    ts: datetime = field(default_factory=_utils.now_utc)
    """The timestamp when the graph run ended."""
    kind: Literal['end'] = 'end'
    """The kind of history step, can be used as a discriminator when deserializing history."""

    id: str = UNSET_SNAPSHOT_ID
    """Unique ID of the snapshot."""

    def __post_init__(self) -> None:
        if self.id == UNSET_SNAPSHOT_ID:
            self.id = self.node.get_snapshot_id()

    @property
    def node(self) -> End[RunEndT]:
        """Shim to get the [`result`][pydantic_graph.persistence.EndSnapshot.result].

        Useful to allow `[snapshot.node for snapshot in persistence.history]`.
        """
        return self.result

```

#### state

```python
state: StateT

```

The state of the graph at the end of the run.

#### result

```python
result: End[RunEndT]

```

The result of the graph run.

#### ts

```python
ts: datetime = field(default_factory=now_utc)

```

The timestamp when the graph run ended.

#### kind

```python
kind: Literal['end'] = 'end'

```

The kind of history step, can be used as a discriminator when deserializing history.

#### id

```python
id: str = UNSET_SNAPSHOT_ID

```

Unique ID of the snapshot.

#### node

```python
node: End[RunEndT]

```

Shim to get the result.

Useful to allow `[snapshot.node for snapshot in persistence.history]`.
