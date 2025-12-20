## Server Instructions

MCP servers can provide instructions during initialization that give context about how to best interact with the server's tools. These instructions are accessible via the instructions property after the server connection is established.

[Learn about Gateway](../../gateway) mcp_server_instructions.py

```python
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStreamableHTTP

server = MCPServerStreamableHTTP('http://localhost:8000/mcp')
agent = Agent('gateway/openai:gpt-5', toolsets=[server])

@agent.instructions
async def mcp_server_instructions():
    return server.instructions  # (1)!

async def main():
    result = await agent.run('What is 7 plus 5?')
    print(result.output)
    #> The answer is 12.

```

1. The server connection is guaranteed to be established by this point, so `server.instructions` is available.

mcp_server_instructions.py

```python
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStreamableHTTP

server = MCPServerStreamableHTTP('http://localhost:8000/mcp')
agent = Agent('openai:gpt-5', toolsets=[server])

@agent.instructions
async def mcp_server_instructions():
    return server.instructions  # (1)!

async def main():
    result = await agent.run('What is 7 plus 5?')
    print(result.output)
    #> The answer is 12.

```

1. The server connection is guaranteed to be established by this point, so `server.instructions` is available.
