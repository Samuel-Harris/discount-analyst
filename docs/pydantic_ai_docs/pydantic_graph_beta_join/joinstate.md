### JoinState

The state of a join during graph execution associated to a particular fork run.

Source code in `pydantic_graph/pydantic_graph/beta/join.py`

```python
@dataclass
class JoinState:
    """The state of a join during graph execution associated to a particular fork run."""

    current: Any
    downstream_fork_stack: ForkStack
    cancelled_sibling_tasks: bool = False

```
