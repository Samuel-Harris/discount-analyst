### Edge

Annotation to apply a label to an edge in a graph.

Source code in `pydantic_graph/pydantic_graph/nodes.py`

```python
@dataclass(frozen=True)
class Edge:
    """Annotation to apply a label to an edge in a graph."""

    label: str | None
    """Label for the edge."""

```

#### label

```python
label: str | None

```

Label for the edge.
