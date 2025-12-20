## MCP Sampling

What is MCP Sampling?

In MCP [sampling](https://modelcontextprotocol.io/docs/concepts/sampling) is a system by which an MCP server can make LLM calls via the MCP client - effectively proxying requests to an LLM via the client over whatever transport is being used.

Sampling is extremely useful when MCP servers need to use Gen AI but you don't want to provision them each with their own LLM credentials or when a public MCP server would like the connecting client to pay for LLM calls.

Confusingly it has nothing to do with the concept of "sampling" in observability, or frankly the concept of "sampling" in any other domain.

Sampling Diagram

Here's a mermaid diagram that may or may not make the data flow clearer:

```
sequenceDiagram
    participant LLM
    participant MCP_Client as MCP client
    participant MCP_Server as MCP server

    MCP_Client->>LLM: LLM call
    LLM->>MCP_Client: LLM tool call response

    MCP_Client->>MCP_Server: tool call
    MCP_Server->>MCP_Client: sampling "create message"

    MCP_Client->>LLM: LLM call
    LLM->>MCP_Client: LLM text response

    MCP_Client->>MCP_Server: sampling response
    MCP_Server->>MCP_Client: tool call response
```

Pydantic AI supports sampling as both a client and server. See the [server](../server/#mcp-sampling) documentation for details on how to use sampling within a server.

Sampling is automatically supported by Pydantic AI agents when they act as a client.

To be able to use sampling, an MCP server instance needs to have a sampling_model set. This can be done either directly on the server using the constructor keyword argument or the property, or by using agent.set_mcp_sampling_model() to set the agent's model or one specified as an argument as the sampling model on all MCP servers registered with that agent.

Let's say we have an MCP server that wants to use sampling (in this case to generate an SVG as per the tool arguments).

Sampling MCP Server generate_svg.py

````python
import re
from pathlib import Path

from mcp import SamplingMessage
from mcp.server.fastmcp import Context, FastMCP
from mcp.types import TextContent

app = FastMCP()


@app.tool()
async def image_generator(ctx: Context, subject: str, style: str) -> str:
    prompt = f'{subject=} {style=}'
    # `ctx.session.create_message` is the sampling call
    result = await ctx.session.create_message(
        [SamplingMessage(role='user', content=TextContent(type='text', text=prompt))],
        max_tokens=1_024,
        system_prompt='Generate an SVG image as per the user input',
    )
    assert isinstance(result.content, TextContent)

    path = Path(f'{subject}_{style}.svg')
    # remove triple backticks if the svg was returned within markdown
    if m := re.search(r'^```\w*$(.+?)```$', result.content.text, re.S | re.M):
        path.write_text(m.group(1), encoding='utf-8')
    else:
        path.write_text(result.content.text, encoding='utf-8')
    return f'See {path}'


if __name__ == '__main__':
    # run the server via stdio
    app.run()

````

Using this server with an `Agent` will automatically allow sampling:

sampling_mcp_client.py

```python
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio

server = MCPServerStdio('python', args=['generate_svg.py'])
agent = Agent('openai:gpt-5', toolsets=[server])


async def main():
    agent.set_mcp_sampling_model()
    result = await agent.run('Create an image of a robot in a punk style.')
    print(result.output)
    #> Image file written to robot_punk.svg.

```

_(This example is complete, it can be run "as is")_

You can disallow sampling by setting allow_sampling=False when creating the server reference, e.g.:

sampling_disallowed.py

```python
from pydantic_ai.mcp import MCPServerStdio

server = MCPServerStdio(
    'python',
    args=['generate_svg.py'],
    allow_sampling=False,
)

```
