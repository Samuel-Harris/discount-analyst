## Using Tool Prefixes to Avoid Naming Conflicts

When connecting to multiple MCP servers that might provide tools with the same name, you can use the `tool_prefix` parameter to avoid naming conflicts. This parameter adds a prefix to all tool names from a specific server.

This allows you to use multiple servers that might have overlapping tool names without conflicts:

[Learn about Gateway](../../gateway) mcp_tool_prefix_http_client.py

```python
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerSSE
