### Usage

[Learn about Gateway](../gateway) mcp_server_anthropic.py

```python
from pydantic_ai import Agent, MCPServerTool

agent = Agent(
    'gateway/anthropic:claude-sonnet-4-5',
    builtin_tools=[
        MCPServerTool(
            id='deepwiki',
            url='https://mcp.deepwiki.com/mcp',  # (1)
        )
    ]
)

result = agent.run_sync('Tell me about the pydantic/pydantic-ai repo.')
print(result.output)
"""
The pydantic/pydantic-ai repo is a Python agent framework for building Generative AI applications.
"""

```

1. The [DeepWiki MCP server](https://docs.devin.ai/work-with-devin/deepwiki-mcp) does not require authorization.

mcp_server_anthropic.py

```python
from pydantic_ai import Agent, MCPServerTool

agent = Agent(
    'anthropic:claude-sonnet-4-5',
    builtin_tools=[
        MCPServerTool(
            id='deepwiki',
            url='https://mcp.deepwiki.com/mcp',  # (1)
        )
    ]
)

result = agent.run_sync('Tell me about the pydantic/pydantic-ai repo.')
print(result.output)
"""
The pydantic/pydantic-ai repo is a Python agent framework for building Generative AI applications.
"""

```

1. The [DeepWiki MCP server](https://docs.devin.ai/work-with-devin/deepwiki-mcp) does not require authorization.

_(This example is complete, it can be run "as is")_

With OpenAI, you must use their Responses API to access the MCP server tool:

[Learn about Gateway](../gateway) mcp_server_openai.py

```python
from pydantic_ai import Agent, MCPServerTool

agent = Agent(
    'gateway/openai-responses:gpt-5',
    builtin_tools=[
        MCPServerTool(
            id='deepwiki',
            url='https://mcp.deepwiki.com/mcp',  # (1)
        )
    ]
)

result = agent.run_sync('Tell me about the pydantic/pydantic-ai repo.')
print(result.output)
"""
The pydantic/pydantic-ai repo is a Python agent framework for building Generative AI applications.
"""

```

1. The [DeepWiki MCP server](https://docs.devin.ai/work-with-devin/deepwiki-mcp) does not require authorization.

mcp_server_openai.py

```python
from pydantic_ai import Agent, MCPServerTool

agent = Agent(
    'openai-responses:gpt-5',
    builtin_tools=[
        MCPServerTool(
            id='deepwiki',
            url='https://mcp.deepwiki.com/mcp',  # (1)
        )
    ]
)

result = agent.run_sync('Tell me about the pydantic/pydantic-ai repo.')
print(result.output)
"""
The pydantic/pydantic-ai repo is a Python agent framework for building Generative AI applications.
"""

```

1. The [DeepWiki MCP server](https://docs.devin.ai/work-with-devin/deepwiki-mcp) does not require authorization.

_(This example is complete, it can be run "as is")_
