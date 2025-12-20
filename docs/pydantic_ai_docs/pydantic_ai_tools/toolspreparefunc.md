### ToolsPrepareFunc

```python
ToolsPrepareFunc: TypeAlias = Callable[
    [RunContext[AgentDepsT], list["ToolDefinition"]],
    Awaitable["list[ToolDefinition] | None"],
]

```

Definition of a function that can prepare the tool definition of all tools for each step. This is useful if you want to customize the definition of multiple tools or you want to register a subset of tools for a given step.

Example â€” here `turn_on_strict_if_openai` is valid as a `ToolsPrepareFunc`:

```python
from dataclasses import replace

from pydantic_ai import Agent, RunContext
from pydantic_ai.tools import ToolDefinition


async def turn_on_strict_if_openai(
    ctx: RunContext[None], tool_defs: list[ToolDefinition]
) -> list[ToolDefinition] | None:
    if ctx.model.system == 'openai':
        return [replace(tool_def, strict=True) for tool_def in tool_defs]
    return tool_defs

agent = Agent('openai:gpt-4o', prepare_tools=turn_on_strict_if_openai)

```

Usage `ToolsPrepareFunc[AgentDepsT]`.
