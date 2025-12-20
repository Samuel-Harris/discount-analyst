## Agent delegation

"Agent delegation" refers to the scenario where an agent delegates work to another agent, then takes back control when the delegate agent (the agent called from within a tool) finishes. If you want to hand off control to another agent completely, without coming back to the first agent, you can use an [output function](../output/#output-functions).

Since agents are stateless and designed to be global, you do not need to include the agent itself in agent [dependencies](../dependencies/).

You'll generally want to pass ctx.usage to the usage keyword argument of the delegate agent run so usage within that run counts towards the total usage of the parent agent run.

Multiple models

Agent delegation doesn't need to use the same model for each agent. If you choose to use different models within a run, calculating the monetary cost from the final result.usage() of the run will not be possible, but you can still use UsageLimits â€” including `request_limit`, `total_tokens_limit`, and `tool_calls_limit` â€” to avoid unexpected costs or runaway tool loops.

[Learn about Gateway](../gateway) agent_delegation_simple.py

```python
from pydantic_ai import Agent, RunContext, UsageLimits

joke_selection_agent = Agent(  # (1)!
    'gateway/openai:gpt-5',
    system_prompt=(
        'Use the `joke_factory` to generate some jokes, then choose the best. '
        'You must return just a single joke.'
    ),
)
joke_generation_agent = Agent(  # (2)!
    'gateway/google-gla:gemini-2.5-flash', output_type=list[str]
)


@joke_selection_agent.tool
async def joke_factory(ctx: RunContext[None], count: int) -> list[str]:
    r = await joke_generation_agent.run(  # (3)!
        f'Please generate {count} jokes.',
        usage=ctx.usage,  # (4)!
    )
    return r.output  # (5)!


result = joke_selection_agent.run_sync(
    'Tell me a joke.',
    usage_limits=UsageLimits(request_limit=5, total_tokens_limit=500),
)
print(result.output)
#> Did you hear about the toothpaste scandal? They called it Colgate.
print(result.usage())
#> RunUsage(input_tokens=204, output_tokens=24, requests=3, tool_calls=1)

```

1. The "parent" or controlling agent.
1. The "delegate" agent, which is called from within a tool of the parent agent.
1. Call the delegate agent from within a tool of the parent agent.
1. Pass the usage from the parent agent to the delegate agent so the final result.usage() includes the usage from both agents.
1. Since the function returns `list[str]`, and the `output_type` of `joke_generation_agent` is also `list[str]`, we can simply return `r.output` from the tool.

agent_delegation_simple.py

```python
from pydantic_ai import Agent, RunContext, UsageLimits

joke_selection_agent = Agent(  # (1)!
    'openai:gpt-5',
    system_prompt=(
        'Use the `joke_factory` to generate some jokes, then choose the best. '
        'You must return just a single joke.'
    ),
)
joke_generation_agent = Agent(  # (2)!
    'google-gla:gemini-2.5-flash', output_type=list[str]
)


@joke_selection_agent.tool
async def joke_factory(ctx: RunContext[None], count: int) -> list[str]:
    r = await joke_generation_agent.run(  # (3)!
        f'Please generate {count} jokes.',
        usage=ctx.usage,  # (4)!
    )
    return r.output  # (5)!


result = joke_selection_agent.run_sync(
    'Tell me a joke.',
    usage_limits=UsageLimits(request_limit=5, total_tokens_limit=500),
)
print(result.output)
#> Did you hear about the toothpaste scandal? They called it Colgate.
print(result.usage())
#> RunUsage(input_tokens=204, output_tokens=24, requests=3, tool_calls=1)

```

1. The "parent" or controlling agent.
1. The "delegate" agent, which is called from within a tool of the parent agent.
1. Call the delegate agent from within a tool of the parent agent.
1. Pass the usage from the parent agent to the delegate agent so the final result.usage() includes the usage from both agents.
1. Since the function returns `list[str]`, and the `output_type` of `joke_generation_agent` is also `list[str]`, we can simply return `r.output` from the tool.

_(This example is complete, it can be run "as is")_

The control flow for this example is pretty simple and can be summarised as follows:

```
graph TD
  START --> joke_selection_agent
  joke_selection_agent --> joke_factory["joke_factory (tool)"]
  joke_factory --> joke_generation_agent
  joke_generation_agent --> joke_factory
  joke_factory --> joke_selection_agent
  joke_selection_agent --> END
```
