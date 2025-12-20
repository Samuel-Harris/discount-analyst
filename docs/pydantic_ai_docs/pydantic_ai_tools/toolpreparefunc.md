### ToolPrepareFunc

```python
ToolPrepareFunc: TypeAlias = Callable[
    [RunContext[AgentDepsT], "ToolDefinition"],
    Awaitable["ToolDefinition | None"],
]

```

Definition of a function that can prepare a tool definition at call time.

See [tool docs](../../tools-advanced/#tool-prepare) for more information.

Example â€” here `only_if_42` is valid as a `ToolPrepareFunc`:

```python
from pydantic_ai import RunContext, Tool
from pydantic_ai.tools import ToolDefinition

async def only_if_42(
    ctx: RunContext[int], tool_def: ToolDefinition
) -> ToolDefinition | None:
    if ctx.deps == 42:
        return tool_def

def hitchhiker(ctx: RunContext[int], answer: str) -> str:
    return f'{ctx.deps} {answer}'

hitchhiker = Tool(hitchhiker, prepare=only_if_42)

```

Usage `ToolPrepareFunc[AgentDepsT]`.
