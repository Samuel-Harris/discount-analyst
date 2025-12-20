### JoinNode

Bases: `BaseNode[StateT, DepsT, Any]`

A base node that represents a join item with bound inputs.

JoinNode bridges between the v1 and v2 graph execution systems by wrapping a Join with bound inputs in a BaseNode interface. It is not meant to be run directly but rather used to indicate transitions to v2-style steps.

Source code in `pydantic_graph/pydantic_graph/beta/join.py`

```python
@dataclass
class JoinNode(BaseNode[StateT, DepsT, Any]):
    """A base node that represents a join item with bound inputs.

    JoinNode bridges between the v1 and v2 graph execution systems by wrapping
    a [`Join`][pydantic_graph.beta.join.Join] with bound inputs in a BaseNode interface.
    It is not meant to be run directly but rather used to indicate transitions
    to v2-style steps.
    """

    join: Join[StateT, DepsT, Any, Any]
    """The step to execute."""

    inputs: Any
    """The inputs bound to this step."""

    async def run(self, ctx: GraphRunContext[StateT, DepsT]) -> BaseNode[StateT, DepsT, Any] | End[Any]:
        """Attempt to run the join node.

        Args:
            ctx: The graph execution context

        Returns:
            The result of step execution

        Raises:
            NotImplementedError: Always raised as StepNode is not meant to be run directly
        """
        raise NotImplementedError(
            '`JoinNode` is not meant to be run directly, it is meant to be used in `BaseNode` subclasses to indicate a transition to v2-style steps.'
        )

```

#### join

```python
join: Join[StateT, DepsT, Any, Any]

```

The step to execute.

#### inputs

```python
inputs: Any

```

The inputs bound to this step.

#### run

```python
run(
    ctx: GraphRunContext[StateT, DepsT],
) -> BaseNode[StateT, DepsT, Any] | End[Any]

```

Attempt to run the join node.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `ctx` | `GraphRunContext[StateT, DepsT]` | The graph execution context | _required_ |

Returns:

| Type | Description | | --- | --- | | `BaseNode[StateT, DepsT, Any] | End[Any]` | The result of step execution |

Raises:

| Type | Description | | --- | --- | | `NotImplementedError` | Always raised as StepNode is not meant to be run directly |

Source code in `pydantic_graph/pydantic_graph/beta/join.py`

```python
async def run(self, ctx: GraphRunContext[StateT, DepsT]) -> BaseNode[StateT, DepsT, Any] | End[Any]:
    """Attempt to run the join node.

    Args:
        ctx: The graph execution context

    Returns:
        The result of step execution

    Raises:
        NotImplementedError: Always raised as StepNode is not meant to be run directly
    """
    raise NotImplementedError(
        '`JoinNode` is not meant to be run directly, it is meant to be used in `BaseNode` subclasses to indicate a transition to v2-style steps.'
    )

```
