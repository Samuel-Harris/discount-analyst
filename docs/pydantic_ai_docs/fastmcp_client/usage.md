## Usage

A `FastMCPToolset` can then be created from:

- A FastMCP Server: `FastMCPToolset(fastmcp.FastMCP('my_server'))`
- A FastMCP Client: `FastMCPToolset(fastmcp.Client(...))`
- A FastMCP Transport: `FastMCPToolset(fastmcp.StdioTransport(command='uvx', args=['mcp-run-python', 'stdio']))`
- A Streamable HTTP URL: `FastMCPToolset('http://localhost:8000/mcp')`
- An HTTP SSE URL: `FastMCPToolset('http://localhost:8000/sse')`
- A Python Script: `FastMCPToolset('my_server.py')`
- A Node.js Script: `FastMCPToolset('my_server.js')`
- A JSON MCP Configuration: `FastMCPToolset({'mcpServers': {'my_server': {'command': 'uvx', 'args': ['mcp-run-python', 'stdio']}}})`

If you already have a [FastMCP Server](https://gofastmcp.com/servers) in the same codebase as your Pydantic AI agent, you can create a `FastMCPToolset` directly from it and save agent a network round trip:

[Learn about Gateway](../../gateway)

```python
from fastmcp import FastMCP

from pydantic_ai import Agent
from pydantic_ai.toolsets.fastmcp import FastMCPToolset

fastmcp_server = FastMCP('my_server')
@fastmcp_server.tool()
async def add(a: int, b: int) -> int:
    return a + b

toolset = FastMCPToolset(fastmcp_server)

agent = Agent('gateway/openai:gpt-5', toolsets=[toolset])

async def main():
    result = await agent.run('What is 7 plus 5?')
    print(result.output)
    #> The answer is 12.

```

```python
from fastmcp import FastMCP

from pydantic_ai import Agent
from pydantic_ai.toolsets.fastmcp import FastMCPToolset

fastmcp_server = FastMCP('my_server')
@fastmcp_server.tool()
async def add(a: int, b: int) -> int:
    return a + b

toolset = FastMCPToolset(fastmcp_server)

agent = Agent('openai:gpt-5', toolsets=[toolset])

async def main():
    result = await agent.run('What is 7 plus 5?')
    print(result.output)
    #> The answer is 12.

```

_(This example is complete, it can be run "as is" â€” you'll need to add `asyncio.run(main())` to run `main`)_

Connecting your agent to a Streamable HTTP MCP Server is as simple as:

[Learn about Gateway](../../gateway)

```python
from pydantic_ai import Agent
from pydantic_ai.toolsets.fastmcp import FastMCPToolset

toolset = FastMCPToolset('http://localhost:8000/mcp')

agent = Agent('gateway/openai:gpt-5', toolsets=[toolset])

```

```python
from pydantic_ai import Agent
from pydantic_ai.toolsets.fastmcp import FastMCPToolset

toolset = FastMCPToolset('http://localhost:8000/mcp')

agent = Agent('openai:gpt-5', toolsets=[toolset])

```

_(This example is complete, it can be run "as is" â€” you'll need to add `asyncio.run(main())` to run `main`)_

You can also create a `FastMCPToolset` from a JSON MCP Configuration:

[Learn about Gateway](../../gateway)

```python
from pydantic_ai import Agent
from pydantic_ai.toolsets.fastmcp import FastMCPToolset

mcp_config = {
    'mcpServers': {
        'time_mcp_server': {
            'command': 'uvx',
            'args': ['mcp-run-python', 'stdio']
        }
    }
}

toolset = FastMCPToolset(mcp_config)

agent = Agent('gateway/openai:gpt-5', toolsets=[toolset])

```

```python
from pydantic_ai import Agent
from pydantic_ai.toolsets.fastmcp import FastMCPToolset

mcp_config = {
    'mcpServers': {
        'time_mcp_server': {
            'command': 'uvx',
            'args': ['mcp-run-python', 'stdio']
        }
    }
}

toolset = FastMCPToolset(mcp_config)

agent = Agent('openai:gpt-5', toolsets=[toolset])

```

_(This example is complete, it can be run "as is" â€” you'll need to add `asyncio.run(main())` to run `main`)_
