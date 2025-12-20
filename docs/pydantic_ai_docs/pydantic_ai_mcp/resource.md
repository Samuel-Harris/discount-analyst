### Resource

Bases: `BaseResource`

A resource that can be read from an MCP server.

See the [resources in the MCP specification](https://modelcontextprotocol.io/specification/2025-06-18/server/resources).

Source code in `pydantic_ai_slim/pydantic_ai/mcp.py`

```python
@dataclass(repr=False, kw_only=True)
class Resource(BaseResource):
    """A resource that can be read from an MCP server.

    See the [resources in the MCP specification](https://modelcontextprotocol.io/specification/2025-06-18/server/resources).
    """

    uri: str
    """The URI of the resource."""

    size: int | None = None
    """The size of the raw resource content in bytes (before base64 encoding), if known."""

    @classmethod
    def from_mcp_sdk(cls, mcp_resource: mcp_types.Resource) -> Resource:
        """Convert from MCP SDK Resource to PydanticAI Resource.

        Args:
            mcp_resource: The MCP SDK Resource object.
        """
        return cls(
            uri=str(mcp_resource.uri),
            name=mcp_resource.name,
            title=mcp_resource.title,
            description=mcp_resource.description,
            mime_type=mcp_resource.mimeType,
            size=mcp_resource.size,
            annotations=ResourceAnnotations.from_mcp_sdk(mcp_resource.annotations)
            if mcp_resource.annotations
            else None,
            metadata=mcp_resource.meta,
        )

```

#### uri

```python
uri: str

```

The URI of the resource.

#### size

```python
size: int | None = None

```

The size of the raw resource content in bytes (before base64 encoding), if known.

#### from_mcp_sdk

```python
from_mcp_sdk(mcp_resource: Resource) -> Resource

```

Convert from MCP SDK Resource to PydanticAI Resource.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `mcp_resource` | `Resource` | The MCP SDK Resource object. | _required_ |

Source code in `pydantic_ai_slim/pydantic_ai/mcp.py`

```python
@classmethod
def from_mcp_sdk(cls, mcp_resource: mcp_types.Resource) -> Resource:
    """Convert from MCP SDK Resource to PydanticAI Resource.

    Args:
        mcp_resource: The MCP SDK Resource object.
    """
    return cls(
        uri=str(mcp_resource.uri),
        name=mcp_resource.name,
        title=mcp_resource.title,
        description=mcp_resource.description,
        mime_type=mcp_resource.mimeType,
        size=mcp_resource.size,
        annotations=ResourceAnnotations.from_mcp_sdk(mcp_resource.annotations)
        if mcp_resource.annotations
        else None,
        metadata=mcp_resource.meta,
    )

```
