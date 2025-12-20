### SSE Client

MCPServerSSE connects over HTTP using the [HTTP + Server Sent Events transport](https://spec.modelcontextprotocol.io/specification/2024-11-05/basic/transports/#http-with-sse) to a server.

Note

The SSE transport in MCP is deprecated, you should use Streamable HTTP instead.

Before creating the SSE client, we need to run a server that supports the SSE transport.

sse_server.py

```python
from mcp.server.fastmcp import FastMCP

app = FastMCP()

@app.tool()
def add(a: int, b: int) -> int:
    return a + b

if __name__ == '__main__':
    app.run(transport='sse')

```

Then we can create the client:

[Learn about Gateway](../../gateway) mcp_sse_client.py

```python
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerSSE

server = MCPServerSSE('http://localhost:3001/sse')  # (1)!
agent = Agent('gateway/openai:gpt-5', toolsets=[server])  # (2)!


async def main():
    result = await agent.run('What is 7 plus 5?')
    print(result.output)
    #> The answer is 12.

```

1. Define the MCP server with the URL used to connect.
1. Create an agent with the MCP server attached.

mcp_sse_client.py

```python
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerSSE

server = MCPServerSSE('http://localhost:3001/sse')  # (1)!
agent = Agent('openai:gpt-5', toolsets=[server])  # (2)!


async def main():
    result = await agent.run('What is 7 plus 5?')
    print(result.output)
    #> The answer is 12.

```

1. Define the MCP server with the URL used to connect.
1. Create an agent with the MCP server attached.

_(This example is complete, it can be run "as is" â€” you'll need to add `asyncio.run(main())` to run `main`)_
