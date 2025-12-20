[FastMCP](https://gofastmcp.com/) is a higher-level MCP framework that bills itself as "The fast, Pythonic way to build MCP servers and clients." It supports additional capabilities on top of the MCP specification like [Tool Transformation](https://gofastmcp.com/patterns/tool-transformation), [OAuth](https://gofastmcp.com/clients/auth/oauth), and more.

As an alternative to Pydantic AI's standard [`MCPServer` MCP client](../client/) built on the [MCP SDK](https://github.com/modelcontextprotocol/python-sdk), you can use the FastMCPToolset [toolset](../../toolsets/) that leverages the [FastMCP Client](https://gofastmcp.com/clients/) to connect to local and remote MCP servers, whether or not they're built using [FastMCP Server](https://gofastmcp.com/servers/).

Note that it does not yet support integration elicitation or sampling, which are supported by the [standard `MCPServer` client](../client/).
