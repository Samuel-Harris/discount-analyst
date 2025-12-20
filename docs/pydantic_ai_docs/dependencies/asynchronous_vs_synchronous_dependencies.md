### Asynchronous vs. Synchronous dependencies

[System prompt functions](../agents/#system-prompts), [function tools](../tools/) and [output validators](../output/#output-validator-functions) are all run in the async context of an agent run.

If these functions are not coroutines (e.g. `async def`) they are called with run_in_executor in a thread pool. It's therefore marginally preferable to use `async` methods where dependencies perform IO, although synchronous dependencies should work fine too.

`run` vs. `run_sync` and Asynchronous vs. Synchronous dependencies

Whether you use synchronous or asynchronous dependencies is completely independent of whether you use `run` or `run_sync` â€” `run_sync` is just a wrapper around `run` and agents are always run in an async context.

Here's the same example as above, but with a synchronous dependency:

[Learn about Gateway](../gateway) sync_dependencies.py

```python
from dataclasses import dataclass

import httpx

from pydantic_ai import Agent, RunContext


@dataclass
class MyDeps:
    api_key: str
    http_client: httpx.Client  # (1)!


agent = Agent(
    'gateway/openai:gpt-5',
    deps_type=MyDeps,
)


@agent.system_prompt
def get_system_prompt(ctx: RunContext[MyDeps]) -> str:  # (2)!
    response = ctx.deps.http_client.get(
        'https://example.com', headers={'Authorization': f'Bearer {ctx.deps.api_key}'}
    )
    response.raise_for_status()
    return f'Prompt: {response.text}'


async def main():
    deps = MyDeps('foobar', httpx.Client())
    result = await agent.run(
        'Tell me a joke.',
        deps=deps,
    )
    print(result.output)
    #> Did you hear about the toothpaste scandal? They called it Colgate.

```

1. Here we use a synchronous `httpx.Client` instead of an asynchronous `httpx.AsyncClient`.
1. To match the synchronous dependency, the system prompt function is now a plain function, not a coroutine.

sync_dependencies.py

```python
from dataclasses import dataclass

import httpx

from pydantic_ai import Agent, RunContext


@dataclass
class MyDeps:
    api_key: str
    http_client: httpx.Client  # (1)!


agent = Agent(
    'openai:gpt-5',
    deps_type=MyDeps,
)


@agent.system_prompt
def get_system_prompt(ctx: RunContext[MyDeps]) -> str:  # (2)!
    response = ctx.deps.http_client.get(
        'https://example.com', headers={'Authorization': f'Bearer {ctx.deps.api_key}'}
    )
    response.raise_for_status()
    return f'Prompt: {response.text}'


async def main():
    deps = MyDeps('foobar', httpx.Client())
    result = await agent.run(
        'Tell me a joke.',
        deps=deps,
    )
    print(result.output)
    #> Did you hear about the toothpaste scandal? They called it Colgate.

```

1. Here we use a synchronous `httpx.Client` instead of an asynchronous `httpx.AsyncClient`.
1. To match the synchronous dependency, the system prompt function is now a plain function, not a coroutine.

_(This example is complete, it can be run "as is" â€” you'll need to add `asyncio.run(main())` to run `main`)_
