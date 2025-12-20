### NodeStep

Bases: `Step[StateT, DepsT, Any, BaseNode[StateT, DepsT, Any] | End[Any]]`

A step that wraps a BaseNode type for execution.

NodeStep allows v1-style BaseNode classes to be used as steps in the v2 graph execution system. It validates that the input is of the expected node type and runs it with the appropriate graph context.

Source code in `pydantic_graph/pydantic_graph/beta/step.py`

```python
class NodeStep(Step[StateT, DepsT, Any, BaseNode[StateT, DepsT, Any] | End[Any]]):
    """A step that wraps a BaseNode type for execution.

    NodeStep allows v1-style BaseNode classes to be used as steps in the
    v2 graph execution system. It validates that the input is of the expected
    node type and runs it with the appropriate graph context.
    """

    node_type: type[BaseNode[StateT, DepsT, Any]]
    """The BaseNode type this step executes."""

    def __init__(
        self,
        node_type: type[BaseNode[StateT, DepsT, Any]],
        *,
        id: NodeID | None = None,
        label: str | None = None,
    ):
        """Initialize a node step.

        Args:
            node_type: The BaseNode class this step will execute
            id: Optional unique identifier, defaults to the node's get_node_id()
            label: Optional human-readable label for this step
        """
        super().__init__(
            id=id or NodeID(node_type.get_node_id()),
            call=self._call_node,
            label=label,
        )
        # `type[BaseNode[StateT, DepsT, Any]]` could actually be a `typing._GenericAlias` like `pydantic_ai._agent_graph.UserPromptNode[~DepsT, ~OutputT]`,
        # so we get the origin to get to the actual class
        self.node_type = get_origin(node_type) or node_type

    async def _call_node(self, ctx: StepContext[StateT, DepsT, Any]) -> BaseNode[StateT, DepsT, Any] | End[Any]:
        """Execute the wrapped node with the step context.

        Args:
            ctx: The step context containing the node instance to run

        Returns:
            The result of running the node, either another BaseNode or End

        Raises:
            ValueError: If the input node is not of the expected type
        """
        node = ctx.inputs
        if not isinstance(node, self.node_type):
            raise ValueError(f'Node {node} is not of type {self.node_type}')  # pragma: no cover
        node = cast(BaseNode[StateT, DepsT, Any], node)
        return await node.run(GraphRunContext(state=ctx.state, deps=ctx.deps))

```

#### **init**

```python
__init__(
    node_type: type[BaseNode[StateT, DepsT, Any]],
    *,
    id: NodeID | None = None,
    label: str | None = None
)

```

Initialize a node step.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `node_type` | `type[BaseNode[StateT, DepsT, Any]]` | The BaseNode class this step will execute | _required_ | | `id` | `NodeID | None` | Optional unique identifier, defaults to the node's get_node_id() | `None` | | `label` | `str | None` | Optional human-readable label for this step | `None` |

Source code in `pydantic_graph/pydantic_graph/beta/step.py`

```python
def __init__(
    self,
    node_type: type[BaseNode[StateT, DepsT, Any]],
    *,
    id: NodeID | None = None,
    label: str | None = None,
):
    """Initialize a node step.

    Args:
        node_type: The BaseNode class this step will execute
        id: Optional unique identifier, defaults to the node's get_node_id()
        label: Optional human-readable label for this step
    """
    super().__init__(
        id=id or NodeID(node_type.get_node_id()),
        call=self._call_node,
        label=label,
    )
    # `type[BaseNode[StateT, DepsT, Any]]` could actually be a `typing._GenericAlias` like `pydantic_ai._agent_graph.UserPromptNode[~DepsT, ~OutputT]`,
    # so we get the origin to get to the actual class
    self.node_type = get_origin(node_type) or node_type

```

#### node_type

```python
node_type: type[BaseNode[StateT, DepsT, Any]] = (
    get_origin(node_type) or node_type
)

```

The BaseNode type this step executes.
