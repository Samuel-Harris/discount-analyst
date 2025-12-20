### load_mcp_servers

```python
load_mcp_servers(
    config_path: str | Path,
) -> list[
    MCPServerStdio | MCPServerStreamableHTTP | MCPServerSSE
]

```

Load MCP servers from a configuration file.

Environment variables can be referenced in the configuration file using:

- `${VAR_NAME}` syntax - expands to the value of VAR_NAME, raises error if not defined
- `${VAR_NAME:-default}` syntax - expands to VAR_NAME if set, otherwise uses the default value

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `config_path` | `str | Path` | The path to the configuration file. | _required_ |

Returns:

| Type | Description | | --- | --- | | `list[MCPServerStdio | MCPServerStreamableHTTP | MCPServerSSE]` | A list of MCP servers. |

Raises:

| Type | Description | | --- | --- | | `FileNotFoundError` | If the configuration file does not exist. | | `ValidationError` | If the configuration file does not match the schema. | | `ValueError` | If an environment variable referenced in the configuration is not defined and no default value is provided. |

Source code in `pydantic_ai_slim/pydantic_ai/mcp.py`

```python
def load_mcp_servers(config_path: str | Path) -> list[MCPServerStdio | MCPServerStreamableHTTP | MCPServerSSE]:
    """Load MCP servers from a configuration file.

    Environment variables can be referenced in the configuration file using:
    - `${VAR_NAME}` syntax - expands to the value of VAR_NAME, raises error if not defined
    - `${VAR_NAME:-default}` syntax - expands to VAR_NAME if set, otherwise uses the default value

    Args:
        config_path: The path to the configuration file.

    Returns:
        A list of MCP servers.

    Raises:
        FileNotFoundError: If the configuration file does not exist.
        ValidationError: If the configuration file does not match the schema.
        ValueError: If an environment variable referenced in the configuration is not defined and no default value is provided.
    """
    config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f'Config file {config_path} not found')

    config_data = pydantic_core.from_json(config_path.read_bytes())
    expanded_config_data = _expand_env_vars(config_data)
    config = MCPServerConfig.model_validate(expanded_config_data)

    servers: list[MCPServerStdio | MCPServerStreamableHTTP | MCPServerSSE] = []
    for name, server in config.mcp_servers.items():
        server.id = name
        server.tool_prefix = name
        servers.append(server)

    return servers

```
