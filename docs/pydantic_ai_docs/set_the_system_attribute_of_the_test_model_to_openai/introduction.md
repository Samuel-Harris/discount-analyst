test_model._system = 'openai'

agent.run_sync('testing with openai...')
assert test_model.last_model_request_parameters.function_tools[0].strict

```

_(This example is complete, it can be run "as is")_

Here's another example that conditionally filters out the tools by name if the dependency (`ctx.deps`) is `True`:

agent_prepare_tools_filter_out.py

```python
from pydantic_ai import Agent, RunContext, Tool, ToolDefinition


def launch_potato(target: str) -> str:
    return f'Potato launched at {target}!'


async def filter_out_tools_by_name(
    ctx: RunContext[bool], tool_defs: list[ToolDefinition]
) -> list[ToolDefinition] | None:
    if ctx.deps:
        return [tool_def for tool_def in tool_defs if tool_def.name != 'launch_potato']
    return tool_defs


agent = Agent(
    'test',
    tools=[Tool(launch_potato)],
    prepare_tools=filter_out_tools_by_name,
    deps_type=bool,
)

result = agent.run_sync('testing...', deps=False)
print(result.output)
#> {"launch_potato":"Potato launched at a!"}
result = agent.run_sync('testing...', deps=True)
print(result.output)
#> success (no tool calls)

```

_(This example is complete, it can be run "as is")_

You can use `prepare_tools` to:

- Dynamically enable or disable tools based on the current model, dependencies, or other context
- Modify tool definitions globally (e.g., set all tools to strict mode, change descriptions, etc.)

If both per-tool `prepare` and agent-wide `prepare_tools` are used, the per-tool `prepare` is applied first to each tool, and then `prepare_tools` is called with the resulting list of tool definitions.
