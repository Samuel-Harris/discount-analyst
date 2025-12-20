### GraphRunContext

Bases: `Generic[StateT, DepsT]`

Context for a graph.

Source code in `pydantic_graph/pydantic_graph/nodes.py`

```python
@dataclass(kw_only=True)
class GraphRunContext(Generic[StateT, DepsT]):
    """Context for a graph."""

    state: StateT
    """The state of the graph."""
    deps: DepsT
    """Dependencies for the graph."""

```

#### state

```python
state: StateT

```

The state of the graph.

#### deps

```python
deps: DepsT

```

Dependencies for the graph.
