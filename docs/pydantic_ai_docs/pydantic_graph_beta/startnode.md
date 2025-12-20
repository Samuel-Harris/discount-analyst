### StartNode

Bases: `Generic[OutputT]`

Entry point node for graph execution.

The StartNode represents the beginning of a graph execution flow.

Source code in `pydantic_graph/pydantic_graph/beta/node.py`

```python
class StartNode(Generic[OutputT]):
    """Entry point node for graph execution.

    The StartNode represents the beginning of a graph execution flow.
    """

    id = NodeID('__start__')
    """Fixed identifier for the start node."""

```

#### id

```python
id = NodeID('__start__')

```

Fixed identifier for the start node.
