## Accessing Dependencies

Dependencies are accessed through the RunContext type, this should be the first parameter of system prompt functions etc.

[Learn about Gateway](../gateway) system_prompt_dependencies.py

```python
from dataclasses import dataclass

import httpx

from pydantic_ai import Agent, RunContext


@dataclass
class MyDeps:
    api_key: str
    http_client: httpx.AsyncClient


agent = Agent(
    'gateway/openai:gpt-5',
    deps_type=MyDeps,
)


@agent.system_prompt  # (1)!
async def get_system_prompt(ctx: RunContext[MyDeps]) -> str:  # (2)!
    response = await ctx.deps.http_client.get(  # (3)!
        'https://example.com',
        headers={'Authorization': f'Bearer {ctx.deps.api_key}'},  # (4)!
    )
    response.raise_for_status()
    return f'Prompt: {response.text}'


async def main():
    async with httpx.AsyncClient() as client:
        deps = MyDeps('foobar', client)
        result = await agent.run('Tell me a joke.', deps=deps)
        print(result.output)
        #> Did you hear about the toothpaste scandal? They called it Colgate.

```

1. RunContext may optionally be passed to a system_prompt function as the only argument.
1. RunContext is parameterized with the type of the dependencies, if this type is incorrect, static type checkers will raise an error.
1. Access dependencies through the .deps attribute.
1. Access dependencies through the .deps attribute.

system_prompt_dependencies.py

```python
from dataclasses import dataclass

import httpx

from pydantic_ai import Agent, RunContext


@dataclass
class MyDeps:
    api_key: str
    http_client: httpx.AsyncClient


agent = Agent(
    'openai:gpt-5',
    deps_type=MyDeps,
)


@agent.system_prompt  # (1)!
async def get_system_prompt(ctx: RunContext[MyDeps]) -> str:  # (2)!
    response = await ctx.deps.http_client.get(  # (3)!
        'https://example.com',
        headers={'Authorization': f'Bearer {ctx.deps.api_key}'},  # (4)!
    )
    response.raise_for_status()
    return f'Prompt: {response.text}'


async def main():
    async with httpx.AsyncClient() as client:
        deps = MyDeps('foobar', client)
        result = await agent.run('Tell me a joke.', deps=deps)
        print(result.output)
        #> Did you hear about the toothpaste scandal? They called it Colgate.

```

1. RunContext may optionally be passed to a system_prompt function as the only argument.
1. RunContext is parameterized with the type of the dependencies, if this type is incorrect, static type checkers will raise an error.
1. Access dependencies through the .deps attribute.
1. Access dependencies through the .deps attribute.

_(This example is complete, it can be run "as is" â€” you'll need to add `asyncio.run(main())` to run `main`)_
