### MCP Servers

Pydantic AI provides two toolsets that allow an agent to connect to and call tools on local and remote MCP Servers:

1. `MCPServer`: the [MCP SDK-based Client](../mcp/client/) which offers more direct control by leveraging the MCP SDK directly
1. `FastMCPToolset`: the [FastMCP-based Client](../mcp/fastmcp-client/) which offers additional capabilities like Tool Transformation, simpler OAuth configuration, and more.
