### FullStatePersistence

Bases: `BaseStatePersistence[StateT, RunEndT]`

In memory state persistence that hold a list of snapshots.

Source code in `pydantic_graph/pydantic_graph/persistence/in_mem.py`

```python
@dataclass
class FullStatePersistence(BaseStatePersistence[StateT, RunEndT]):
    """In memory state persistence that hold a list of snapshots."""

    deep_copy: bool = True
    """Whether to deep copy the state and nodes when storing them.

    Defaults to `True` so even if nodes or state are modified after the snapshot is taken,
    the persistence history will record the value at the time of the snapshot.
    """
    history: list[Snapshot[StateT, RunEndT]] = field(default_factory=list)
    """List of snapshots taken during the graph run."""
    _snapshots_type_adapter: pydantic.TypeAdapter[list[Snapshot[StateT, RunEndT]]] | None = field(
        default=None, init=False, repr=False
    )

    async def snapshot_node(self, state: StateT, next_node: BaseNode[StateT, Any, RunEndT]) -> None:
        snapshot = NodeSnapshot(
            state=self._prep_state(state),
            node=next_node.deep_copy() if self.deep_copy else next_node,
        )
        self.history.append(snapshot)

    async def snapshot_node_if_new(
        self, snapshot_id: str, state: StateT, next_node: BaseNode[StateT, Any, RunEndT]
    ) -> None:
        if not any(s.id == snapshot_id for s in self.history):
            await self.snapshot_node(state, next_node)

    async def snapshot_end(self, state: StateT, end: End[RunEndT]) -> None:
        snapshot = EndSnapshot(
            state=self._prep_state(state),
            result=end.deep_copy_data() if self.deep_copy else end,
        )
        self.history.append(snapshot)

    @asynccontextmanager
    async def record_run(self, snapshot_id: str) -> AsyncIterator[None]:
        try:
            snapshot = next(s for s in self.history if s.id == snapshot_id)
        except StopIteration as e:
            raise LookupError(f'No snapshot found with id={snapshot_id!r}') from e

        assert isinstance(snapshot, NodeSnapshot), 'Only NodeSnapshot can be recorded'
        exceptions.GraphNodeStatusError.check(snapshot.status)
        snapshot.status = 'running'
        snapshot.start_ts = _utils.now_utc()
        start = perf_counter()
        try:
            yield
        except Exception:
            snapshot.duration = perf_counter() - start
            snapshot.status = 'error'
            raise
        else:
            snapshot.duration = perf_counter() - start
            snapshot.status = 'success'

    async def load_next(self) -> NodeSnapshot[StateT, RunEndT] | None:
        if snapshot := next((s for s in self.history if isinstance(s, NodeSnapshot) and s.status == 'created'), None):
            snapshot.status = 'pending'
            return copy.deepcopy(snapshot)

    async def load_all(self) -> list[Snapshot[StateT, RunEndT]]:
        return self.history

    def should_set_types(self) -> bool:
        return self._snapshots_type_adapter is None

    def set_types(self, state_type: type[StateT], run_end_type: type[RunEndT]) -> None:
        self._snapshots_type_adapter = build_snapshot_list_type_adapter(state_type, run_end_type)

    def dump_json(self, *, indent: int | None = None) -> bytes:
        """Dump the history to JSON bytes."""
        assert self._snapshots_type_adapter is not None, 'type adapter must be set to use `dump_json`'
        return self._snapshots_type_adapter.dump_json(self.history, indent=indent)

    def load_json(self, json_data: str | bytes | bytearray) -> None:
        """Load the history from JSON."""
        assert self._snapshots_type_adapter is not None, 'type adapter must be set to use `load_json`'
        self.history = self._snapshots_type_adapter.validate_json(json_data)

    def _prep_state(self, state: StateT) -> StateT:
        """Prepare state for snapshot, uses [`copy.deepcopy`][copy.deepcopy] by default."""
        if not self.deep_copy or state is None:
            return state
        else:
            return copy.deepcopy(state)

```

#### deep_copy

```python
deep_copy: bool = True

```

Whether to deep copy the state and nodes when storing them.

Defaults to `True` so even if nodes or state are modified after the snapshot is taken, the persistence history will record the value at the time of the snapshot.

#### history

```python
history: list[Snapshot[StateT, RunEndT]] = field(
    default_factory=list
)

```

List of snapshots taken during the graph run.

#### dump_json

```python
dump_json(*, indent: int | None = None) -> bytes

```

Dump the history to JSON bytes.

Source code in `pydantic_graph/pydantic_graph/persistence/in_mem.py`

```python
def dump_json(self, *, indent: int | None = None) -> bytes:
    """Dump the history to JSON bytes."""
    assert self._snapshots_type_adapter is not None, 'type adapter must be set to use `dump_json`'
    return self._snapshots_type_adapter.dump_json(self.history, indent=indent)

```

#### load_json

```python
load_json(json_data: str | bytes | bytearray) -> None

```

Load the history from JSON.

Source code in `pydantic_graph/pydantic_graph/persistence/in_mem.py`

```python
def load_json(self, json_data: str | bytes | bytearray) -> None:
    """Load the history from JSON."""
    assert self._snapshots_type_adapter is not None, 'type adapter must be set to use `load_json`'
    self.history = self._snapshots_type_adapter.validate_json(json_data)

```
