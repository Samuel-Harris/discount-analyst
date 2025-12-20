### Configuration Format

The configuration file should be a JSON file with an `mcpServers` object containing server definitions. Each server is identified by a unique key and contains the configuration for that server type:

mcp_config.json

```json
{
  "mcpServers": {
    "python-runner": {
      "command": "uv",
      "args": ["run", "mcp-run-python", "stdio"]
    },
    "weather-api": {
      "url": "http://localhost:3001/sse"
    },
    "calculator": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

Note

The MCP server is only inferred to be an SSE server because of the `/sse` suffix. Any other server with the "url" field will be inferred to be a Streamable HTTP server.

We made this decision given that the SSE transport is deprecated.
