## MCP Server

Here's a simple example of a [Python MCP server](https://github.com/modelcontextprotocol/python-sdk) using Pydantic AI within a tool call:

[Learn about Gateway](../../gateway) mcp_server.py

```python
from mcp.server.fastmcp import FastMCP

from pydantic_ai import Agent

server = FastMCP('Pydantic AI Server')
server_agent = Agent(
    'gateway/anthropic:claude-haiku-4-5', system_prompt='always reply in rhyme'
)


@server.tool()
async def poet(theme: str) -> str:
    """Poem generator"""
    r = await server_agent.run(f'write a poem about {theme}')
    return r.output


if __name__ == '__main__':
    server.run()

```

mcp_server.py

```python
from mcp.server.fastmcp import FastMCP

from pydantic_ai import Agent

server = FastMCP('Pydantic AI Server')
server_agent = Agent(
    'anthropic:claude-haiku-4-5', system_prompt='always reply in rhyme'
)


@server.tool()
async def poet(theme: str) -> str:
    """Poem generator"""
    r = await server_agent.run(f'write a poem about {theme}')
    return r.output


if __name__ == '__main__':
    server.run()

```
