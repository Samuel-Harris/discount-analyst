Pydantic AI supports [Model Context Protocol (MCP)](https://modelcontextprotocol.io) in multiple ways:

1. [Agents](../../agents/) can connect to MCP servers and use their tools using three different methods:
   1. Pydantic AI can act as an MCP client and connect directly to local and remote MCP servers. [Learn more](../client/) about MCPServer.
   1. Pydantic AI can use the [FastMCP Client](https://gofastmcp.com/clients/client/) to connect to local and remote MCP servers, whether or not they're built using [FastMCP Server](https://gofastmcp.com/servers). [Learn more](../fastmcp-client/) about FastMCPToolset.
   1. Some model providers can themselves connect to remote MCP servers using a "built-in tool". [Learn more](../../builtin-tools/#mcp-server-tool) about MCPServerTool.
1. Agents can be used within MCP servers. [Learn more](../server/)
