### ServerCapabilities

Capabilities that an MCP server supports.

Source code in `pydantic_ai_slim/pydantic_ai/mcp.py`

```python
@dataclass(repr=False, kw_only=True)
class ServerCapabilities:
    """Capabilities that an MCP server supports."""

    experimental: list[str] | None = None
    """Experimental, non-standard capabilities that the server supports."""

    logging: bool = False
    """Whether the server supports sending log messages to the client."""

    prompts: bool = False
    """Whether the server offers any prompt templates."""

    prompts_list_changed: bool = False
    """Whether the server will emit notifications when the list of prompts changes."""

    resources: bool = False
    """Whether the server offers any resources to read."""

    resources_list_changed: bool = False
    """Whether the server will emit notifications when the list of resources changes."""

    tools: bool = False
    """Whether the server offers any tools to call."""

    tools_list_changed: bool = False
    """Whether the server will emit notifications when the list of tools changes."""

    completions: bool = False
    """Whether the server offers autocompletion suggestions for prompts and resources."""

    __repr__ = _utils.dataclasses_no_defaults_repr

    @classmethod
    def from_mcp_sdk(cls, mcp_capabilities: mcp_types.ServerCapabilities) -> ServerCapabilities:
        """Convert from MCP SDK ServerCapabilities to PydanticAI ServerCapabilities.

        Args:
            mcp_capabilities: The MCP SDK ServerCapabilities object.
        """
        prompts_cap = mcp_capabilities.prompts
        resources_cap = mcp_capabilities.resources
        tools_cap = mcp_capabilities.tools
        return cls(
            experimental=list(mcp_capabilities.experimental.keys()) if mcp_capabilities.experimental else None,
            logging=mcp_capabilities.logging is not None,
            prompts=prompts_cap is not None,
            prompts_list_changed=bool(prompts_cap.listChanged) if prompts_cap else False,
            resources=resources_cap is not None,
            resources_list_changed=bool(resources_cap.listChanged) if resources_cap else False,
            tools=tools_cap is not None,
            tools_list_changed=bool(tools_cap.listChanged) if tools_cap else False,
            completions=mcp_capabilities.completions is not None,
        )

```

#### experimental

```python
experimental: list[str] | None = None

```

Experimental, non-standard capabilities that the server supports.

#### logging

```python
logging: bool = False

```

Whether the server supports sending log messages to the client.

#### prompts

```python
prompts: bool = False

```

Whether the server offers any prompt templates.

#### prompts_list_changed

```python
prompts_list_changed: bool = False

```

Whether the server will emit notifications when the list of prompts changes.

#### resources

```python
resources: bool = False

```

Whether the server offers any resources to read.

#### resources_list_changed

```python
resources_list_changed: bool = False

```

Whether the server will emit notifications when the list of resources changes.

#### tools

```python
tools: bool = False

```

Whether the server offers any tools to call.

#### tools_list_changed

```python
tools_list_changed: bool = False

```

Whether the server will emit notifications when the list of tools changes.

#### completions

```python
completions: bool = False

```

Whether the server offers autocompletion suggestions for prompts and resources.

#### from_mcp_sdk

```python
from_mcp_sdk(
    mcp_capabilities: ServerCapabilities,
) -> ServerCapabilities

```

Convert from MCP SDK ServerCapabilities to PydanticAI ServerCapabilities.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `mcp_capabilities` | `ServerCapabilities` | The MCP SDK ServerCapabilities object. | _required_ |

Source code in `pydantic_ai_slim/pydantic_ai/mcp.py`

```python
@classmethod
def from_mcp_sdk(cls, mcp_capabilities: mcp_types.ServerCapabilities) -> ServerCapabilities:
    """Convert from MCP SDK ServerCapabilities to PydanticAI ServerCapabilities.

    Args:
        mcp_capabilities: The MCP SDK ServerCapabilities object.
    """
    prompts_cap = mcp_capabilities.prompts
    resources_cap = mcp_capabilities.resources
    tools_cap = mcp_capabilities.tools
    return cls(
        experimental=list(mcp_capabilities.experimental.keys()) if mcp_capabilities.experimental else None,
        logging=mcp_capabilities.logging is not None,
        prompts=prompts_cap is not None,
        prompts_list_changed=bool(prompts_cap.listChanged) if prompts_cap else False,
        resources=resources_cap is not None,
        resources_list_changed=bool(resources_cap.listChanged) if resources_cap else False,
        tools=tools_cap is not None,
        tools_list_changed=bool(tools_cap.listChanged) if tools_cap else False,
        completions=mcp_capabilities.completions is not None,
    )

```
