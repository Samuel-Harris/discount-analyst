### Configuration Options

The `MCPServerTool` supports several configuration parameters for custom MCP servers:

[Learn about Gateway](../gateway) mcp_server_configured_url.py

```python
import os

from pydantic_ai import Agent, MCPServerTool

agent = Agent(
    'gateway/openai-responses:gpt-5',
    builtin_tools=[
        MCPServerTool(
            id='github',
            url='https://api.githubcopilot.com/mcp/',
            authorization_token=os.getenv('GITHUB_ACCESS_TOKEN', 'mock-access-token'),  # (1)
            allowed_tools=['search_repositories', 'list_commits'],
            description='GitHub MCP server',
            headers={'X-Custom-Header': 'custom-value'},
        )
    ]
)

result = agent.run_sync('Tell me about the pydantic/pydantic-ai repo.')
print(result.output)
"""
The pydantic/pydantic-ai repo is a Python agent framework for building Generative AI applications.
"""

```

1. The [GitHub MCP server](https://github.com/github/github-mcp-server) requires an authorization token.

mcp_server_configured_url.py

```python
import os

from pydantic_ai import Agent, MCPServerTool

agent = Agent(
    'openai-responses:gpt-5',
    builtin_tools=[
        MCPServerTool(
            id='github',
            url='https://api.githubcopilot.com/mcp/',
            authorization_token=os.getenv('GITHUB_ACCESS_TOKEN', 'mock-access-token'),  # (1)
            allowed_tools=['search_repositories', 'list_commits'],
            description='GitHub MCP server',
            headers={'X-Custom-Header': 'custom-value'},
        )
    ]
)

result = agent.run_sync('Tell me about the pydantic/pydantic-ai repo.')
print(result.output)
"""
The pydantic/pydantic-ai repo is a Python agent framework for building Generative AI applications.
"""

```

1. The [GitHub MCP server](https://github.com/github/github-mcp-server) requires an authorization token.

For OpenAI Responses, you can use a [connector](https://platform.openai.com/docs/guides/tools-connectors-mcp#connectors) by specifying a special `x-openai-connector:` URL:

_(This example is complete, it can be run "as is")_

[Learn about Gateway](../gateway) mcp_server_configured_connector_id.py

```python
import os

from pydantic_ai import Agent, MCPServerTool

agent = Agent(
    'gateway/openai-responses:gpt-5',
    builtin_tools=[
        MCPServerTool(
            id='google-calendar',
            url='x-openai-connector:connector_googlecalendar',
            authorization_token=os.getenv('GOOGLE_API_KEY', 'mock-api-key'), # (1)
        )
    ]
)

result = agent.run_sync('What do I have on my calendar today?')
print(result.output)
#> You're going to spend all day playing with Pydantic AI.

```

1. OpenAI's Google Calendar connector requires an [authorization token](https://platform.openai.com/docs/guides/tools-connectors-mcp#authorizing-a-connector).

mcp_server_configured_connector_id.py

```python
import os

from pydantic_ai import Agent, MCPServerTool

agent = Agent(
    'openai-responses:gpt-5',
    builtin_tools=[
        MCPServerTool(
            id='google-calendar',
            url='x-openai-connector:connector_googlecalendar',
            authorization_token=os.getenv('GOOGLE_API_KEY', 'mock-api-key'), # (1)
        )
    ]
)

result = agent.run_sync('What do I have on my calendar today?')
print(result.output)
#> You're going to spend all day playing with Pydantic AI.

```

1. OpenAI's Google Calendar connector requires an [authorization token](https://platform.openai.com/docs/guides/tools-connectors-mcp#authorizing-a-connector).

_(This example is complete, it can be run "as is")_

#### Provider Support

| Parameter | OpenAI | Anthropic | | --- | --- | --- | | `authorization_token` | âœ… | âœ… | | `allowed_tools` | âœ… | âœ… | | `description` | âœ… | âŒ | | `headers` | âœ… | âŒ |
