### MCPError

Bases: `RuntimeError`

Raised when an MCP server returns an error response.

This exception wraps error responses from MCP servers, following the ErrorData schema from the MCP specification.

Source code in `pydantic_ai_slim/pydantic_ai/mcp.py`

```python
class MCPError(RuntimeError):
    """Raised when an MCP server returns an error response.

    This exception wraps error responses from MCP servers, following the ErrorData schema
    from the MCP specification.
    """

    message: str
    """The error message."""

    code: int
    """The error code returned by the server."""

    data: dict[str, Any] | None
    """Additional information about the error, if provided by the server."""

    def __init__(self, message: str, code: int, data: dict[str, Any] | None = None):
        self.message = message
        self.code = code
        self.data = data
        super().__init__(message)

    @classmethod
    def from_mcp_sdk(cls, error: mcp_exceptions.McpError) -> MCPError:
        """Create an MCPError from an MCP SDK McpError.

        Args:
            error: An McpError from the MCP SDK.
        """
        # Extract error data from the McpError.error attribute
        error_data = error.error
        return cls(message=error_data.message, code=error_data.code, data=error_data.data)

    def __str__(self) -> str:
        if self.data:
            return f'{self.message} (code: {self.code}, data: {self.data})'
        return f'{self.message} (code: {self.code})'

```

#### message

```python
message: str = message

```

The error message.

#### code

```python
code: int = code

```

The error code returned by the server.

#### data

```python
data: dict[str, Any] | None = data

```

Additional information about the error, if provided by the server.

#### from_mcp_sdk

```python
from_mcp_sdk(error: McpError) -> MCPError

```

Create an MCPError from an MCP SDK McpError.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `error` | `McpError` | An McpError from the MCP SDK. | _required_ |

Source code in `pydantic_ai_slim/pydantic_ai/mcp.py`

```python
@classmethod
def from_mcp_sdk(cls, error: mcp_exceptions.McpError) -> MCPError:
    """Create an MCPError from an MCP SDK McpError.

    Args:
        error: An McpError from the MCP SDK.
    """
    # Extract error data from the McpError.error attribute
    error_data = error.error
    return cls(message=error_data.message, code=error_data.code, data=error_data.data)

```
