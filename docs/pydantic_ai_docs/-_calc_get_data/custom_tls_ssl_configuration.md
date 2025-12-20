## Custom TLS / SSL configuration

In some environments you need to tweak how HTTPS connections are established â€“ for example to trust an internal Certificate Authority, present a client certificate for **mTLS**, or (during local development only!) disable certificate verification altogether. All HTTP-based MCP client classes (MCPServerStreamableHTTP and MCPServerSSE) expose an `http_client` parameter that lets you pass your own pre-configured [`httpx.AsyncClient`](https://www.python-httpx.org/async/).

[Learn about Gateway](../../gateway) mcp_custom_tls_client.py

```python
import ssl

import httpx

from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerSSE
