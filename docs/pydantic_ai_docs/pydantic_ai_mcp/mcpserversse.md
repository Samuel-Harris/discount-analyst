### MCPServerSSE

Bases: `_MCPServerHTTP`

An MCP server that connects over streamable HTTP connections.

This class implements the SSE transport from the MCP specification. See <https://spec.modelcontextprotocol.io/specification/2024-11-05/basic/transports/#http-with-sse> for more information.

Note

Using this class as an async context manager will create a new pool of HTTP connections to connect to a server which should already be running.

Example:

```python
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerSSE

server = MCPServerSSE('http://localhost:3001/sse')
agent = Agent('openai:gpt-4o', toolsets=[server])

```

Source code in `pydantic_ai_slim/pydantic_ai/mcp.py`

````python
class MCPServerSSE(_MCPServerHTTP):
    """An MCP server that connects over streamable HTTP connections.

    This class implements the SSE transport from the MCP specification.
    See <https://spec.modelcontextprotocol.io/specification/2024-11-05/basic/transports/#http-with-sse> for more information.

    !!! note
        Using this class as an async context manager will create a new pool of HTTP connections to connect
        to a server which should already be running.

    Example:
    ```python {py="3.10"}
    from pydantic_ai import Agent
    from pydantic_ai.mcp import MCPServerSSE

    server = MCPServerSSE('http://localhost:3001/sse')
    agent = Agent('openai:gpt-4o', toolsets=[server])
    ```
    """

    @classmethod
    def __get_pydantic_core_schema__(cls, _: Any, __: Any) -> CoreSchema:
        return core_schema.no_info_after_validator_function(
            lambda dct: MCPServerSSE(**dct),
            core_schema.typed_dict_schema(
                {
                    'url': core_schema.typed_dict_field(core_schema.str_schema()),
                    'headers': core_schema.typed_dict_field(
                        core_schema.dict_schema(core_schema.str_schema(), core_schema.str_schema()), required=False
                    ),
                }
            ),
        )

    @property
    def _transport_client(self):
        return sse_client  # pragma: no cover

    def __eq__(self, value: object, /) -> bool:
        return super().__eq__(value) and isinstance(value, MCPServerSSE) and self.url == value.url

````
