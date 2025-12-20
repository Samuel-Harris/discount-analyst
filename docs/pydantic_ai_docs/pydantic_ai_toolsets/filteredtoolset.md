### FilteredToolset

Bases: `WrapperToolset[AgentDepsT]`

A toolset that filters the tools it contains using a filter function that takes the agent context and the tool definition.

See [toolset docs](../../toolsets/#filtering-tools) for more information.

Source code in `pydantic_ai_slim/pydantic_ai/toolsets/filtered.py`

```python
@dataclass
class FilteredToolset(WrapperToolset[AgentDepsT]):
    """A toolset that filters the tools it contains using a filter function that takes the agent context and the tool definition.

    See [toolset docs](../toolsets.md#filtering-tools) for more information.
    """

    filter_func: Callable[[RunContext[AgentDepsT], ToolDefinition], bool]

    async def get_tools(self, ctx: RunContext[AgentDepsT]) -> dict[str, ToolsetTool[AgentDepsT]]:
        return {
            name: tool for name, tool in (await super().get_tools(ctx)).items() if self.filter_func(ctx, tool.tool_def)
        }

```
