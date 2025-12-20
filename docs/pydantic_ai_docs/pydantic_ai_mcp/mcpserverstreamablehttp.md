### MCPServerStreamableHTTP

Bases: `_MCPServerHTTP`

An MCP server that connects over HTTP using the Streamable HTTP transport.

This class implements the Streamable HTTP transport from the MCP specification. See <https://modelcontextprotocol.io/introduction#streamable-http> for more information.

Note

Using this class as an async context manager will create a new pool of HTTP connections to connect to a server which should already be running.

Example:

```python
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStreamableHTTP

server = MCPServerStreamableHTTP('http://localhost:8000/mcp')
agent = Agent('openai:gpt-4o', toolsets=[server])

```

Source code in `pydantic_ai_slim/pydantic_ai/mcp.py`

````python
class MCPServerStreamableHTTP(_MCPServerHTTP):
    """An MCP server that connects over HTTP using the Streamable HTTP transport.

    This class implements the Streamable HTTP transport from the MCP specification.
    See <https://modelcontextprotocol.io/introduction#streamable-http> for more information.

    !!! note
        Using this class as an async context manager will create a new pool of HTTP connections to connect
        to a server which should already be running.

    Example:
    ```python {py="3.10"}
    from pydantic_ai import Agent
    from pydantic_ai.mcp import MCPServerStreamableHTTP

    server = MCPServerStreamableHTTP('http://localhost:8000/mcp')
    agent = Agent('openai:gpt-4o', toolsets=[server])
    ```
    """

    @classmethod
    def __get_pydantic_core_schema__(cls, _: Any, __: Any) -> CoreSchema:
        return core_schema.no_info_after_validator_function(
            lambda dct: MCPServerStreamableHTTP(**dct),
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
        return streamablehttp_client

    def __eq__(self, value: object, /) -> bool:
        return super().__eq__(value) and isinstance(value, MCPServerStreamableHTTP) and self.url == value.url

````
