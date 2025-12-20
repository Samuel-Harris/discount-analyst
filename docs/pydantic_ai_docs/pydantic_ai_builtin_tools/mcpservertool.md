### MCPServerTool

Bases: `AbstractBuiltinTool`

A builtin tool that allows your agent to use MCP servers.

Supported by:

- OpenAI Responses
- Anthropic

Source code in `pydantic_ai_slim/pydantic_ai/builtin_tools.py`

```python
@dataclass(kw_only=True)
class MCPServerTool(AbstractBuiltinTool):
    """A builtin tool that allows your agent to use MCP servers.

    Supported by:

    * OpenAI Responses
    * Anthropic
    """

    id: str
    """A unique identifier for the MCP server."""

    url: str
    """The URL of the MCP server to use.

    For OpenAI Responses, it is possible to use `connector_id` by providing it as `x-openai-connector:<connector_id>`.
    """

    authorization_token: str | None = None
    """Authorization header to use when making requests to the MCP server.

    Supported by:

    * OpenAI Responses
    * Anthropic
    """

    description: str | None = None
    """A description of the MCP server.

    Supported by:

    * OpenAI Responses
    """

    allowed_tools: list[str] | None = None
    """A list of tools that the MCP server can use.

    Supported by:

    * OpenAI Responses
    * Anthropic
    """

    headers: dict[str, str] | None = None
    """Optional HTTP headers to send to the MCP server.

    Use for authentication or other purposes.

    Supported by:

    * OpenAI Responses
    """

    kind: str = 'mcp_server'

    @property
    def unique_id(self) -> str:
        return ':'.join([self.kind, self.id])

```

#### id

```python
id: str

```

A unique identifier for the MCP server.

#### url

```python
url: str

```

The URL of the MCP server to use.

For OpenAI Responses, it is possible to use `connector_id` by providing it as `x-openai-connector:<connector_id>`.

#### authorization_token

```python
authorization_token: str | None = None

```

Authorization header to use when making requests to the MCP server.

Supported by:

- OpenAI Responses
- Anthropic

#### description

```python
description: str | None = None

```

A description of the MCP server.

Supported by:

- OpenAI Responses

#### allowed_tools

```python
allowed_tools: list[str] | None = None

```

A list of tools that the MCP server can use.

Supported by:

- OpenAI Responses
- Anthropic

#### headers

```python
headers: dict[str, str] | None = None

```

Optional HTTP headers to send to the MCP server.

Use for authentication or other purposes.

Supported by:

- OpenAI Responses
