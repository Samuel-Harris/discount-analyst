### MCP "stdio" Server

MCP also offers [stdio transport](https://spec.modelcontextprotocol.io/specification/2024-11-05/basic/transports/#stdio) where the server is run as a subprocess and communicates with the client over `stdin` and `stdout`. In this case, you'd use the MCPServerStdio class.

In this example [mcp-run-python](https://github.com/pydantic/mcp-run-python) is used as the MCP server.

[Learn about Gateway](../../gateway) mcp_stdio_client.py

```python
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio

server = MCPServerStdio(  # (1)!
    'uv', args=['run', 'mcp-run-python', 'stdio'], timeout=10
)
agent = Agent('gateway/openai:gpt-5', toolsets=[server])


async def main():
    result = await agent.run('How many days between 2000-01-01 and 2025-03-18?')
    print(result.output)
    #> There are 9,208 days between January 1, 2000, and March 18, 2025.

```

1. See [MCP Run Python](https://github.com/pydantic/mcp-run-python) for more information.

mcp_stdio_client.py

```python
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio

server = MCPServerStdio(  # (1)!
    'uv', args=['run', 'mcp-run-python', 'stdio'], timeout=10
)
agent = Agent('openai:gpt-5', toolsets=[server])


async def main():
    result = await agent.run('How many days between 2000-01-01 and 2025-03-18?')
    print(result.output)
    #> There are 9,208 days between January 1, 2000, and March 18, 2025.

```

1. See [MCP Run Python](https://github.com/pydantic/mcp-run-python) for more information.
