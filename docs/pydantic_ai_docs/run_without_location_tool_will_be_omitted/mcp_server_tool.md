## MCP Server Tool

The MCPServerTool allows your agent to use remote MCP servers with communication handled by the model provider.

This requires the MCP server to live at a public URL the provider can reach and does not support many of the advanced features of Pydantic AI's agent-side [MCP support](../mcp/client/), but can result in optimized context use and caching, and faster performance due to the lack of a round-trip back to Pydantic AI.
