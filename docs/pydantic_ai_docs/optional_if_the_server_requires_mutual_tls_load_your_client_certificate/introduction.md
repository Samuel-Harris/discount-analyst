ssl_ctx.load_cert_chain(certfile='/etc/ssl/certs/client.crt', keyfile='/etc/ssl/private/client.key',)

http_client = httpx.AsyncClient(
    verify=ssl_ctx,
    timeout=httpx.Timeout(10.0),
)

server = MCPServerSSE(
    'http://localhost:3001/sse',
    http_client=http_client,  # (1)!
)
agent = Agent('openai:gpt-5', toolsets=[server])

async def main():
    result = await agent.run('How many days between 2000-01-01 and 2025-03-18?')
    print(result.output)
    #> There are 9,208 days between January 1, 2000, and March 18, 2025.

```

1. When you supply `http_client`, Pydantic AI re-uses this client for every request. Anything supported by **httpx** (`verify`, `cert`, custom proxies, timeouts, etc.) therefore applies to all MCP traffic.
