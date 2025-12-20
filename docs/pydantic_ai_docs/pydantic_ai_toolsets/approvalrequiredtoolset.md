### ApprovalRequiredToolset

Bases: `WrapperToolset[AgentDepsT]`

A toolset that requires (some) calls to tools it contains to be approved.

See [toolset docs](../../toolsets/#requiring-tool-approval) for more information.

Source code in `pydantic_ai_slim/pydantic_ai/toolsets/approval_required.py`

```python
@dataclass
class ApprovalRequiredToolset(WrapperToolset[AgentDepsT]):
    """A toolset that requires (some) calls to tools it contains to be approved.

    See [toolset docs](../toolsets.md#requiring-tool-approval) for more information.
    """

    approval_required_func: Callable[[RunContext[AgentDepsT], ToolDefinition, dict[str, Any]], bool] = (
        lambda ctx, tool_def, tool_args: True
    )

    async def call_tool(
        self, name: str, tool_args: dict[str, Any], ctx: RunContext[AgentDepsT], tool: ToolsetTool[AgentDepsT]
    ) -> Any:
        if not ctx.tool_call_approved and self.approval_required_func(ctx, tool.tool_def, tool_args):
            raise ApprovalRequired

        return await super().call_tool(name, tool_args, ctx, tool)

```
