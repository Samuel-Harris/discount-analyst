### MCPServerHTTP

Bases: `MCPServerSSE`

Deprecated

The `MCPServerHTTP` class is deprecated, use `MCPServerSSE` instead.

An MCP server that connects over HTTP using the old SSE transport.

This class implements the SSE transport from the MCP specification. See <https://spec.modelcontextprotocol.io/specification/2024-11-05/basic/transports/#http-with-sse> for more information.

Note

Using this class as an async context manager will create a new pool of HTTP connections to connect to a server which should already be running.

Example:

```python
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerHTTP

server = MCPServerHTTP('http://localhost:3001/sse')
agent = Agent('openai:gpt-4o', toolsets=[server])

```

Source code in `pydantic_ai_slim/pydantic_ai/mcp.py`

````python
@deprecated('The `MCPServerHTTP` class is deprecated, use `MCPServerSSE` instead.')
class MCPServerHTTP(MCPServerSSE):
    """An MCP server that connects over HTTP using the old SSE transport.

    This class implements the SSE transport from the MCP specification.
    See <https://spec.modelcontextprotocol.io/specification/2024-11-05/basic/transports/#http-with-sse> for more information.

    !!! note
        Using this class as an async context manager will create a new pool of HTTP connections to connect
        to a server which should already be running.

    Example:
    ```python {py="3.10" test="skip"}
    from pydantic_ai import Agent
    from pydantic_ai.mcp import MCPServerHTTP

    server = MCPServerHTTP('http://localhost:3001/sse')
    agent = Agent('openai:gpt-4o', toolsets=[server])
    ```
    """

````
