### Environment Variables

The configuration file supports environment variable expansion using the `${VAR}` and `${VAR:-default}` syntax, [like Claude Code](https://code.claude.com/docs/en/mcp#environment-variable-expansion-in-mcp-json). This is useful for keeping sensitive information like API keys or host names out of your configuration files:

mcp_config_with_env.json

```json
{
  "mcpServers": {
    "python-runner": {
      "command": "${PYTHON_CMD:-python3}",
      "args": ["run", "${MCP_MODULE}", "stdio"],
      "env": {
        "API_KEY": "${MY_API_KEY}"
      }
    },
    "weather-api": {
      "url": "https://${SERVER_HOST:-localhost}:${SERVER_PORT:-8080}/sse"
    }
  }
}
```

When loading this configuration with load_mcp_servers():

- `${VAR}` references will be replaced with the corresponding environment variable values.
- `${VAR:-default}` references will use the environment variable value if set, otherwise the default value.

Warning

If a referenced environment variable using `${VAR}` syntax is not defined, a `ValueError` will be raised. Use the `${VAR:-default}` syntax to provide a fallback value.
