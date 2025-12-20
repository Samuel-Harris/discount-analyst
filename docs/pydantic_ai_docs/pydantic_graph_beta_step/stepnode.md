### StepNode

Bases: `BaseNode[StateT, DepsT, Any]`

A base node that represents a step with bound inputs.

StepNode bridges between the v1 and v2 graph execution systems by wrapping a Step with bound inputs in a BaseNode interface. It is not meant to be run directly but rather used to indicate transitions to v2-style steps.

Source code in `pydantic_graph/pydantic_graph/beta/step.py`

```python
@dataclass
class StepNode(BaseNode[StateT, DepsT, Any]):
    """A base node that represents a step with bound inputs.

    StepNode bridges between the v1 and v2 graph execution systems by wrapping
    a [`Step`][pydantic_graph.beta.step.Step] with bound inputs in a BaseNode interface.
    It is not meant to be run directly but rather used to indicate transitions
    to v2-style steps.
    """

    step: Step[StateT, DepsT, Any, Any]
    """The step to execute."""

    inputs: Any
    """The inputs bound to this step."""

    async def run(self, ctx: GraphRunContext[StateT, DepsT]) -> BaseNode[StateT, DepsT, Any] | End[Any]:
        """Attempt to run the step node.

        Args:
            ctx: The graph execution context

        Returns:
            The result of step execution

        Raises:
            NotImplementedError: Always raised as StepNode is not meant to be run directly
        """
        raise NotImplementedError(
            '`StepNode` is not meant to be run directly, it is meant to be used in `BaseNode` subclasses to indicate a transition to v2-style steps.'
        )

```

#### step

```python
step: Step[StateT, DepsT, Any, Any]

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

Attempt to run the step node.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `ctx` | `GraphRunContext[StateT, DepsT]` | The graph execution context | _required_ |

Returns:

| Type | Description | | --- | --- | | `BaseNode[StateT, DepsT, Any] | End[Any]` | The result of step execution |

Raises:

| Type | Description | | --- | --- | | `NotImplementedError` | Always raised as StepNode is not meant to be run directly |

Source code in `pydantic_graph/pydantic_graph/beta/step.py`

```python
async def run(self, ctx: GraphRunContext[StateT, DepsT]) -> BaseNode[StateT, DepsT, Any] | End[Any]:
    """Attempt to run the step node.

    Args:
        ctx: The graph execution context

    Returns:
        The result of step execution

    Raises:
        NotImplementedError: Always raised as StepNode is not meant to be run directly
    """
    raise NotImplementedError(
        '`StepNode` is not meant to be run directly, it is meant to be used in `BaseNode` subclasses to indicate a transition to v2-style steps.'
    )

```
