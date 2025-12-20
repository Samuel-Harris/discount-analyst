### Agent-wide Dynamic Tools

In addition to per-tool `prepare` methods, you can also define an agent-wide `prepare_tools` function. This function is called at each step of a run and allows you to filter or modify the list of all tool definitions available to the agent for that step. This is especially useful if you want to enable or disable multiple tools at once, or apply global logic based on the current context.

The `prepare_tools` function should be of type ToolsPrepareFunc, which takes the RunContext and a list of ToolDefinition, and returns a new list of tool definitions (or `None` to disable all tools for that step).

Note

The list of tool definitions passed to `prepare_tools` includes both regular function tools and tools from any [toolsets](../toolsets/) registered on the agent, but not [output tools](../output/#tool-output).

To modify output tools, you can set a `prepare_output_tools` function instead.

Here's an example that makes all tools strict if the model is an OpenAI model:

agent_prepare_tools_customize.py

```python
from dataclasses import replace

from pydantic_ai import Agent, RunContext, ToolDefinition
from pydantic_ai.models.test import TestModel


async def turn_on_strict_if_openai(
    ctx: RunContext[None], tool_defs: list[ToolDefinition]
) -> list[ToolDefinition] | None:
    if ctx.model.system == 'openai':
        return [replace(tool_def, strict=True) for tool_def in tool_defs]
    return tool_defs


test_model = TestModel()
agent = Agent(test_model, prepare_tools=turn_on_strict_if_openai)


@agent.tool_plain
def echo(message: str) -> str:
    return message


agent.run_sync('testing...')
assert test_model.last_model_request_parameters.function_tools[0].strict is None
