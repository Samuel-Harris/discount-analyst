### PrefectFunctionToolset

Bases: `PrefectWrapperToolset[AgentDepsT]`

A wrapper for FunctionToolset that integrates with Prefect, turning tool calls into Prefect tasks.

Source code in `pydantic_ai_slim/pydantic_ai/durable_exec/prefect/_function_toolset.py`

```python
class PrefectFunctionToolset(PrefectWrapperToolset[AgentDepsT]):
    """A wrapper for FunctionToolset that integrates with Prefect, turning tool calls into Prefect tasks."""

    def __init__(
        self,
        wrapped: FunctionToolset[AgentDepsT],
        *,
        task_config: TaskConfig,
        tool_task_config: dict[str, TaskConfig | None],
    ):
        super().__init__(wrapped)
        self._task_config = default_task_config | (task_config or {})
        self._tool_task_config = tool_task_config or {}

        @task
        async def _call_tool_task(
            tool_name: str,
            tool_args: dict[str, Any],
            ctx: RunContext[AgentDepsT],
            tool: ToolsetTool[AgentDepsT],
        ) -> Any:
            return await super(PrefectFunctionToolset, self).call_tool(tool_name, tool_args, ctx, tool)

        self._call_tool_task = _call_tool_task

    async def call_tool(
        self,
        name: str,
        tool_args: dict[str, Any],
        ctx: RunContext[AgentDepsT],
        tool: ToolsetTool[AgentDepsT],
    ) -> Any:
        """Call a tool, wrapped as a Prefect task with a descriptive name."""
        # Check if this specific tool has custom config or is disabled
        tool_specific_config = self._tool_task_config.get(name, default_task_config)
        if tool_specific_config is None:
            # None means this tool should not be wrapped as a task
            return await super().call_tool(name, tool_args, ctx, tool)

        # Merge tool-specific config with default config
        merged_config = self._task_config | tool_specific_config

        return await self._call_tool_task.with_options(name=f'Call Tool: {name}', **merged_config)(
            name, tool_args, ctx, tool
        )

```

#### call_tool

```python
call_tool(
    name: str,
    tool_args: dict[str, Any],
    ctx: RunContext[AgentDepsT],
    tool: ToolsetTool[AgentDepsT],
) -> Any

```

Call a tool, wrapped as a Prefect task with a descriptive name.

Source code in `pydantic_ai_slim/pydantic_ai/durable_exec/prefect/_function_toolset.py`

```python
async def call_tool(
    self,
    name: str,
    tool_args: dict[str, Any],
    ctx: RunContext[AgentDepsT],
    tool: ToolsetTool[AgentDepsT],
) -> Any:
    """Call a tool, wrapped as a Prefect task with a descriptive name."""
    # Check if this specific tool has custom config or is disabled
    tool_specific_config = self._tool_task_config.get(name, default_task_config)
    if tool_specific_config is None:
        # None means this tool should not be wrapped as a task
        return await super().call_tool(name, tool_args, ctx, tool)

    # Merge tool-specific config with default config
    merged_config = self._task_config | tool_specific_config

    return await self._call_tool_task.with_options(name=f'Call Tool: {name}', **merged_config)(
        name, tool_args, ctx, tool
    )

```
