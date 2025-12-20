### ResourceAnnotations

Additional properties describing MCP entities.

See the [resource annotations in the MCP specification](https://modelcontextprotocol.io/specification/2025-06-18/server/resources#annotations).

Source code in `pydantic_ai_slim/pydantic_ai/mcp.py`

```python
@dataclass(repr=False, kw_only=True)
class ResourceAnnotations:
    """Additional properties describing MCP entities.

    See the [resource annotations in the MCP specification](https://modelcontextprotocol.io/specification/2025-06-18/server/resources#annotations).
    """

    audience: list[mcp_types.Role] | None = None
    """Intended audience for this entity."""

    priority: Annotated[float, Field(ge=0.0, le=1.0)] | None = None
    """Priority level for this entity, ranging from 0.0 to 1.0."""

    __repr__ = _utils.dataclasses_no_defaults_repr

    @classmethod
    def from_mcp_sdk(cls, mcp_annotations: mcp_types.Annotations) -> ResourceAnnotations:
        """Convert from MCP SDK Annotations to ResourceAnnotations.

        Args:
            mcp_annotations: The MCP SDK annotations object.
        """
        return cls(audience=mcp_annotations.audience, priority=mcp_annotations.priority)

```

#### audience

```python
audience: list[Role] | None = None

```

Intended audience for this entity.

#### priority

```python
priority: Annotated[float, Field(ge=0.0, le=1.0)] | None = (
    None
)

```

Priority level for this entity, ranging from 0.0 to 1.0.

#### from_mcp_sdk

```python
from_mcp_sdk(
    mcp_annotations: Annotations,
) -> ResourceAnnotations

```

Convert from MCP SDK Annotations to ResourceAnnotations.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `mcp_annotations` | `Annotations` | The MCP SDK annotations object. | _required_ |

Source code in `pydantic_ai_slim/pydantic_ai/mcp.py`

```python
@classmethod
def from_mcp_sdk(cls, mcp_annotations: mcp_types.Annotations) -> ResourceAnnotations:
    """Convert from MCP SDK Annotations to ResourceAnnotations.

    Args:
        mcp_annotations: The MCP SDK annotations object.
    """
    return cls(audience=mcp_annotations.audience, priority=mcp_annotations.priority)

```
