### JoinItem

An item representing data flowing into a join operation.

JoinItem carries input data from a parallel execution path to a join node, along with metadata about which execution 'fork' it originated from.

Source code in `pydantic_graph/pydantic_graph/beta/graph.py`

```python
@dataclass
class JoinItem:
    """An item representing data flowing into a join operation.

    JoinItem carries input data from a parallel execution path to a join
    node, along with metadata about which execution 'fork' it originated from.
    """

    join_id: JoinID
    """The ID of the join node this item is targeting."""

    inputs: Any
    """The input data for the join operation."""

    fork_stack: ForkStack
    """The stack of ForkStackItems that led to producing this join item."""

```

#### join_id

```python
join_id: JoinID

```

The ID of the join node this item is targeting.

#### inputs

```python
inputs: Any

```

The input data for the join operation.

#### fork_stack

```python
fork_stack: ForkStack

```

The stack of ForkStackItems that led to producing this join item.
