### GraphTaskRequest

A request to run a task representing the execution of a node in the graph.

GraphTaskRequest encapsulates all the information needed to execute a specific node, including its inputs and the fork context it's executing within.

Source code in `pydantic_graph/pydantic_graph/beta/graph.py`

```python
@dataclass
class GraphTaskRequest:
    """A request to run a task representing the execution of a node in the graph.

    GraphTaskRequest encapsulates all the information needed to execute a specific
    node, including its inputs and the fork context it's executing within.
    """

    node_id: NodeID
    """The ID of the node to execute."""

    inputs: Any
    """The input data for the node."""

    fork_stack: ForkStack = field(repr=False)
    """Stack of forks that have been entered.

    Used by the GraphRun to decide when to proceed through joins.
    """

```

#### node_id

```python
node_id: NodeID

```

The ID of the node to execute.

#### inputs

```python
inputs: Any

```

The input data for the node.

#### fork_stack

```python
fork_stack: ForkStack = field(repr=False)

```

Stack of forks that have been entered.

Used by the GraphRun to decide when to proceed through joins.
