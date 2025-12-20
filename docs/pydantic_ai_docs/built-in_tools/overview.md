## Overview

Pydantic AI supports the following built-in tools:

- **WebSearchTool**: Allows agents to search the web
- **CodeExecutionTool**: Enables agents to execute code in a secure environment
- **ImageGenerationTool**: Enables agents to generate images
- **WebFetchTool**: Enables agents to fetch web pages
- **MemoryTool**: Enables agents to use memory
- **MCPServerTool**: Enables agents to use remote MCP servers with communication handled by the model provider

These tools are passed to the agent via the `builtin_tools` parameter and are executed by the model provider's infrastructure.

Provider Support

Not all model providers support built-in tools. If you use a built-in tool with an unsupported provider, Pydantic AI will raise a UserError when you try to run the agent.

If a provider supports a built-in tool that is not currently supported by Pydantic AI, please file an issue.
