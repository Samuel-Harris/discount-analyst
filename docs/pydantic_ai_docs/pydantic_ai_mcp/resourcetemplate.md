### ResourceTemplate

Bases: `BaseResource`

A template for parameterized resources on an MCP server.

See the [resource templates in the MCP specification](https://modelcontextprotocol.io/specification/2025-06-18/server/resources#resource-templates).

Source code in `pydantic_ai_slim/pydantic_ai/mcp.py`

```python
@dataclass(repr=False, kw_only=True)
class ResourceTemplate(BaseResource):
    """A template for parameterized resources on an MCP server.

    See the [resource templates in the MCP specification](https://modelcontextprotocol.io/specification/2025-06-18/server/resources#resource-templates).
    """

    uri_template: str
    """URI template (RFC 6570) for constructing resource URIs."""

    @classmethod
    def from_mcp_sdk(cls, mcp_template: mcp_types.ResourceTemplate) -> ResourceTemplate:
        """Convert from MCP SDK ResourceTemplate to PydanticAI ResourceTemplate.

        Args:
            mcp_template: The MCP SDK ResourceTemplate object.
        """
        return cls(
            uri_template=mcp_template.uriTemplate,
            name=mcp_template.name,
            title=mcp_template.title,
            description=mcp_template.description,
            mime_type=mcp_template.mimeType,
            annotations=ResourceAnnotations.from_mcp_sdk(mcp_template.annotations)
            if mcp_template.annotations
            else None,
            metadata=mcp_template.meta,
        )

```

#### uri_template

```python
uri_template: str

```

URI template (RFC 6570) for constructing resource URIs.

#### from_mcp_sdk

```python
from_mcp_sdk(
    mcp_template: ResourceTemplate,
) -> ResourceTemplate

```

Convert from MCP SDK ResourceTemplate to PydanticAI ResourceTemplate.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `mcp_template` | `ResourceTemplate` | The MCP SDK ResourceTemplate object. | _required_ |

Source code in `pydantic_ai_slim/pydantic_ai/mcp.py`

```python
@classmethod
def from_mcp_sdk(cls, mcp_template: mcp_types.ResourceTemplate) -> ResourceTemplate:
    """Convert from MCP SDK ResourceTemplate to PydanticAI ResourceTemplate.

    Args:
        mcp_template: The MCP SDK ResourceTemplate object.
    """
    return cls(
        uri_template=mcp_template.uriTemplate,
        name=mcp_template.name,
        title=mcp_template.title,
        description=mcp_template.description,
        mime_type=mcp_template.mimeType,
        annotations=ResourceAnnotations.from_mcp_sdk(mcp_template.annotations)
        if mcp_template.annotations
        else None,
        metadata=mcp_template.meta,
    )

```
