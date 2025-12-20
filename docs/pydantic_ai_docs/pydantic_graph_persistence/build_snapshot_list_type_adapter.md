### build_snapshot_list_type_adapter

```python
build_snapshot_list_type_adapter(
    state_t: type[StateT], run_end_t: type[RunEndT]
) -> TypeAdapter[list[Snapshot[StateT, RunEndT]]]

```

Build a type adapter for a list of snapshots.

This method should be called from within set_types where context variables will be set such that Pydantic can create a schema for NodeSnapshot.node.

Source code in `pydantic_graph/pydantic_graph/persistence/__init__.py`

```python
def build_snapshot_list_type_adapter(
    state_t: type[StateT], run_end_t: type[RunEndT]
) -> pydantic.TypeAdapter[list[Snapshot[StateT, RunEndT]]]:
    """Build a type adapter for a list of snapshots.

    This method should be called from within
    [`set_types`][pydantic_graph.persistence.BaseStatePersistence.set_types]
    where context variables will be set such that Pydantic can create a schema for
    [`NodeSnapshot.node`][pydantic_graph.persistence.NodeSnapshot.node].
    """
    return pydantic.TypeAdapter(list[Annotated[Snapshot[state_t, run_end_t], pydantic.Discriminator('kind')]])

```

In memory state persistence.

This module provides simple in memory state persistence for graphs.
