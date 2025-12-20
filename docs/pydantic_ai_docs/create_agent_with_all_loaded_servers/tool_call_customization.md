## Tool call customization

The MCP servers provide the ability to set a `process_tool_call` which allows the customization of tool call requests and their responses.

A common use case for this is to inject metadata to the requests which the server call needs:

mcp_process_tool_call.py

```python
from typing import Any

from pydantic_ai import Agent, RunContext
from pydantic_ai.mcp import CallToolFunc, MCPServerStdio, ToolResult
from pydantic_ai.models.test import TestModel


async def process_tool_call(
    ctx: RunContext[int],
    call_tool: CallToolFunc,
    name: str,
    tool_args: dict[str, Any],
) -> ToolResult:
    """A tool call processor that passes along the deps."""
    return await call_tool(name, tool_args, {'deps': ctx.deps})


server = MCPServerStdio('python', args=['mcp_server.py'], process_tool_call=process_tool_call)
agent = Agent(
    model=TestModel(call_tools=['echo_deps']),
    deps_type=int,
    toolsets=[server]
)


async def main():
    result = await agent.run('Echo with deps set to 42', deps=42)
    print(result.output)
    #> {"echo_deps":{"echo":"This is an echo message","deps":42}}

```

How to access the metadata is MCP server SDK specific. For example with the [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk), it is accessible via the [`ctx: Context`](https://github.com/modelcontextprotocol/python-sdk#context) argument that can be included on tool call handlers:

mcp_server.py

```python
from typing import Any

from mcp.server.fastmcp import Context, FastMCP
from mcp.server.session import ServerSession

mcp = FastMCP('Pydantic AI MCP Server')
log_level = 'unset'


@mcp.tool()
async def echo_deps(ctx: Context[ServerSession, None]) -> dict[str, Any]:
    """Echo the run context.

    Args:
        ctx: Context object containing request and session information.

    Returns:
        Dictionary with an echo message and the deps.
    """
    await ctx.info('This is an info message')

    deps: Any = getattr(ctx.request_context.meta, 'deps')
    return {'echo': 'This is an echo message', 'deps': deps}

if __name__ == '__main__':
    mcp.run()

```
