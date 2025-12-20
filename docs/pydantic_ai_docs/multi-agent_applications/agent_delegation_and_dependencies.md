### Agent delegation and dependencies

Generally the delegate agent needs to either have the same [dependencies](../dependencies/) as the calling agent, or dependencies which are a subset of the calling agent's dependencies.

Initializing dependencies

We say "generally" above since there's nothing to stop you initializing dependencies within a tool call and therefore using interdependencies in a delegate agent that are not available on the parent, this should often be avoided since it can be significantly slower than reusing connections etc. from the parent agent.

[Learn about Gateway](../gateway) agent_delegation_deps.py

```python
from dataclasses import dataclass

import httpx

from pydantic_ai import Agent, RunContext


@dataclass
class ClientAndKey:  # (1)!
    http_client: httpx.AsyncClient
    api_key: str


joke_selection_agent = Agent(
    'gateway/openai:gpt-5',
    deps_type=ClientAndKey,  # (2)!
    system_prompt=(
        'Use the `joke_factory` tool to generate some jokes on the given subject, '
        'then choose the best. You must return just a single joke.'
    ),
)
joke_generation_agent = Agent(
    'gateway/google-gla:gemini-2.5-flash',
    deps_type=ClientAndKey,  # (4)!
    output_type=list[str],
    system_prompt=(
        'Use the "get_jokes" tool to get some jokes on the given subject, '
        'then extract each joke into a list.'
    ),
)


@joke_selection_agent.tool
async def joke_factory(ctx: RunContext[ClientAndKey], count: int) -> list[str]:
    r = await joke_generation_agent.run(
        f'Please generate {count} jokes.',
        deps=ctx.deps,  # (3)!
        usage=ctx.usage,
    )
    return r.output


@joke_generation_agent.tool  # (5)!
async def get_jokes(ctx: RunContext[ClientAndKey], count: int) -> str:
    response = await ctx.deps.http_client.get(
        'https://example.com',
        params={'count': count},
        headers={'Authorization': f'Bearer {ctx.deps.api_key}'},
    )
    response.raise_for_status()
    return response.text


async def main():
    async with httpx.AsyncClient() as client:
        deps = ClientAndKey(client, 'foobar')
        result = await joke_selection_agent.run('Tell me a joke.', deps=deps)
        print(result.output)
        #> Did you hear about the toothpaste scandal? They called it Colgate.
        print(result.usage())  # (6)!
        #> RunUsage(input_tokens=309, output_tokens=32, requests=4, tool_calls=2)

```

1. Define a dataclass to hold the client and API key dependencies.
1. Set the `deps_type` of the calling agent â€” `joke_selection_agent` here.
1. Pass the dependencies to the delegate agent's run method within the tool call.
1. Also set the `deps_type` of the delegate agent â€” `joke_generation_agent` here.
1. Define a tool on the delegate agent that uses the dependencies to make an HTTP request.
1. Usage now includes 4 requests â€” 2 from the calling agent and 2 from the delegate agent.

agent_delegation_deps.py

```python
from dataclasses import dataclass

import httpx

from pydantic_ai import Agent, RunContext


@dataclass
class ClientAndKey:  # (1)!
    http_client: httpx.AsyncClient
    api_key: str


joke_selection_agent = Agent(
    'openai:gpt-5',
    deps_type=ClientAndKey,  # (2)!
    system_prompt=(
        'Use the `joke_factory` tool to generate some jokes on the given subject, '
        'then choose the best. You must return just a single joke.'
    ),
)
joke_generation_agent = Agent(
    'google-gla:gemini-2.5-flash',
    deps_type=ClientAndKey,  # (4)!
    output_type=list[str],
    system_prompt=(
        'Use the "get_jokes" tool to get some jokes on the given subject, '
        'then extract each joke into a list.'
    ),
)


@joke_selection_agent.tool
async def joke_factory(ctx: RunContext[ClientAndKey], count: int) -> list[str]:
    r = await joke_generation_agent.run(
        f'Please generate {count} jokes.',
        deps=ctx.deps,  # (3)!
        usage=ctx.usage,
    )
    return r.output


@joke_generation_agent.tool  # (5)!
async def get_jokes(ctx: RunContext[ClientAndKey], count: int) -> str:
    response = await ctx.deps.http_client.get(
        'https://example.com',
        params={'count': count},
        headers={'Authorization': f'Bearer {ctx.deps.api_key}'},
    )
    response.raise_for_status()
    return response.text


async def main():
    async with httpx.AsyncClient() as client:
        deps = ClientAndKey(client, 'foobar')
        result = await joke_selection_agent.run('Tell me a joke.', deps=deps)
        print(result.output)
        #> Did you hear about the toothpaste scandal? They called it Colgate.
        print(result.usage())  # (6)!
        #> RunUsage(input_tokens=309, output_tokens=32, requests=4, tool_calls=2)

```

1. Define a dataclass to hold the client and API key dependencies.
1. Set the `deps_type` of the calling agent â€” `joke_selection_agent` here.
1. Pass the dependencies to the delegate agent's run method within the tool call.
1. Also set the `deps_type` of the delegate agent â€” `joke_generation_agent` here.
1. Define a tool on the delegate agent that uses the dependencies to make an HTTP request.
1. Usage now includes 4 requests â€” 2 from the calling agent and 2 from the delegate agent.

_(This example is complete, it can be run "as is" â€” you'll need to add `asyncio.run(main())` to run `main`)_

This example shows how even a fairly simple agent delegation can lead to a complex control flow:

```
graph TD
  START --> joke_selection_agent
  joke_selection_agent --> joke_factory["joke_factory (tool)"]
  joke_factory --> joke_generation_agent
  joke_generation_agent --> get_jokes["get_jokes (tool)"]
  get_jokes --> http_request["HTTP request"]
  http_request --> get_jokes
  get_jokes --> joke_generation_agent
  joke_generation_agent --> joke_factory
  joke_factory --> joke_selection_agent
  joke_selection_agent --> END
```
