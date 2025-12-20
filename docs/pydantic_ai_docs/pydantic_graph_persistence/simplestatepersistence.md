### SimpleStatePersistence

Bases: `BaseStatePersistence[StateT, RunEndT]`

Simple in memory state persistence that just hold the latest snapshot.

If no state persistence implementation is provided when running a graph, this is used by default.

Source code in `pydantic_graph/pydantic_graph/persistence/in_mem.py`

```python
@dataclass
class SimpleStatePersistence(BaseStatePersistence[StateT, RunEndT]):
    """Simple in memory state persistence that just hold the latest snapshot.

    If no state persistence implementation is provided when running a graph, this is used by default.
    """

    last_snapshot: Snapshot[StateT, RunEndT] | None = None
    """The last snapshot."""

    async def snapshot_node(self, state: StateT, next_node: BaseNode[StateT, Any, RunEndT]) -> None:
        self.last_snapshot = NodeSnapshot(state=state, node=next_node)

    async def snapshot_node_if_new(
        self, snapshot_id: str, state: StateT, next_node: BaseNode[StateT, Any, RunEndT]
    ) -> None:
        if self.last_snapshot and self.last_snapshot.id == snapshot_id:
            return  # pragma: no cover
        else:
            await self.snapshot_node(state, next_node)

    async def snapshot_end(self, state: StateT, end: End[RunEndT]) -> None:
        self.last_snapshot = EndSnapshot(state=state, result=end)

    @asynccontextmanager
    async def record_run(self, snapshot_id: str) -> AsyncIterator[None]:
        if self.last_snapshot is None or snapshot_id != self.last_snapshot.id:
            raise LookupError(f'No snapshot found with id={snapshot_id!r}')

        assert isinstance(self.last_snapshot, NodeSnapshot), 'Only NodeSnapshot can be recorded'
        exceptions.GraphNodeStatusError.check(self.last_snapshot.status)
        self.last_snapshot.status = 'running'
        self.last_snapshot.start_ts = _utils.now_utc()

        start = perf_counter()
        try:
            yield
        except Exception:  # pragma: no cover
            self.last_snapshot.duration = perf_counter() - start
            self.last_snapshot.status = 'error'
            raise
        else:
            self.last_snapshot.duration = perf_counter() - start
            self.last_snapshot.status = 'success'

    async def load_next(self) -> NodeSnapshot[StateT, RunEndT] | None:
        if isinstance(self.last_snapshot, NodeSnapshot) and self.last_snapshot.status == 'created':
            self.last_snapshot.status = 'pending'
            return copy.deepcopy(self.last_snapshot)

    async def load_all(self) -> list[Snapshot[StateT, RunEndT]]:
        raise NotImplementedError('load is not supported for SimpleStatePersistence')

```

#### last_snapshot

```python
last_snapshot: Snapshot[StateT, RunEndT] | None = None

```

The last snapshot.
