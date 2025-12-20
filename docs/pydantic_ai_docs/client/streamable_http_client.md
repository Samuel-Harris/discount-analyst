### Streamable HTTP Client

MCPServerStreamableHTTP connects over HTTP using the [Streamable HTTP](https://modelcontextprotocol.io/introduction#streamable-http) transport to a server.

Note

MCPServerStreamableHTTP requires an MCP server to be running and accepting HTTP connections before running the agent. Running the server is not managed by Pydantic AI.

Before creating the Streamable HTTP client, we need to run a server that supports the Streamable HTTP transport.

streamable_http_server.py

```python
from mcp.server.fastmcp import FastMCP

app = FastMCP()

@app.tool()
def add(a: int, b: int) -> int:
    return a + b

if __name__ == '__main__':
    app.run(transport='streamable-http')

```

Then we can create the client:

[Learn about Gateway](../../gateway) mcp_streamable_http_client.py

```python
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStreamableHTTP

server = MCPServerStreamableHTTP('http://localhost:8000/mcp')  # (1)!
agent = Agent('gateway/openai:gpt-5', toolsets=[server])  # (2)!

async def main():
    result = await agent.run('What is 7 plus 5?')
    print(result.output)
    #> The answer is 12.

```

1. Define the MCP server with the URL used to connect.
1. Create an agent with the MCP server attached.

mcp_streamable_http_client.py

```python
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStreamableHTTP

server = MCPServerStreamableHTTP('http://localhost:8000/mcp')  # (1)!
agent = Agent('openai:gpt-5', toolsets=[server])  # (2)!

async def main():
    result = await agent.run('What is 7 plus 5?')
    print(result.output)
    #> The answer is 12.

```

1. Define the MCP server with the URL used to connect.
1. Create an agent with the MCP server attached.

_(This example is complete, it can be run "as is" â€” you'll need to add `asyncio.run(main())` to run `main`)_

**What's happening here?**

- The model receives the prompt "What is 7 plus 5?"
- The model decides "Oh, I've got this `add` tool, that will be a good way to answer this question"
- The model returns a tool call
- Pydantic AI sends the tool call to the MCP server using the Streamable HTTP transport
- The model is called again with the return value of running the `add` tool (12)
- The model returns the final answer

You can visualise this clearly, and even see the tool call, by adding three lines of code to instrument the example with [logfire](https://logfire.pydantic.dev/docs):

mcp_sse_client_logfire.py

```python
import logfire

logfire.configure()
logfire.instrument_pydantic_ai()

```
