## Resources

MCP servers can provide [resources](https://modelcontextprotocol.io/docs/concepts/resources) - files, data, or content that can be accessed by the client. Resources in MCP are application-driven, with host applications determining how to incorporate context manually, based on their needs. This means they will _not_ be exposed to the LLM automatically (unless a tool returns a `ResourceLink` or `EmbeddedResource`).

Pydantic AI provides methods to discover and read resources from MCP servers:

- list_resources() - List all available resources on the server
- list_resource_templates() - List resource templates with parameter placeholders
- read_resource(uri) - Read the contents of a specific resource by URI

Resources are automatically converted: text content is returned as `str`, and binary content is returned as BinaryContent.

Before consuming resources, we need to run a server that exposes some:

mcp_resource_server.py

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP('Pydantic AI MCP Server')
log_level = 'unset'


@mcp.resource('resource://user_name.txt', mime_type='text/plain')
async def user_name_resource() -> str:
    return 'Alice'


if __name__ == '__main__':
    mcp.run()

```

Then we can create the client:

mcp_resources.py

```python
import asyncio

from pydantic_ai.mcp import MCPServerStdio


async def main():
    server = MCPServerStdio('python', args=['-m', 'mcp_resource_server'])

    async with server:
        # List all available resources
        resources = await server.list_resources()
        for resource in resources:
            print(f' - {resource.name}: {resource.uri} ({resource.mime_type})')
            #>  - user_name_resource: resource://user_name.txt (text/plain)

        # Read a text resource
        user_name = await server.read_resource('resource://user_name.txt')
        print(f'Text content: {user_name}')
        #> Text content: Alice


if __name__ == '__main__':
    asyncio.run(main())

```

_(This example is complete, it can be run "as is")_
