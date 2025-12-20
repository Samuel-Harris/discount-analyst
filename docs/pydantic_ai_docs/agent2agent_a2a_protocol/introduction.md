## Introduction

Agents are Pydantic AI's primary interface for interacting with LLMs.

In some use cases a single Agent will control an entire application or component, but multiple agents can also interact to embody more complex workflows.

The Agent class has full API documentation, but conceptually you can think of an agent as a container for:

| **Component** | **Description** | | --- | --- | | [Instructions](#instructions) | A set of instructions for the LLM written by the developer. | | [Function tool(s)](../tools/) and [toolsets](../toolsets/) | Functions that the LLM may call to get information while generating a response. | | [Structured output type](../output/) | The structured datatype the LLM must return at the end of a run, if specified. | | [Dependency type constraint](../dependencies/) | Dynamic instructions functions, tools, and output functions may all use dependencies when they're run. | | [LLM model](../api/models/base/) | Optional default LLM model associated with the agent. Can also be specified when running the agent. | | [Model Settings](#additional-configuration) | Optional default model settings to help fine tune requests. Can also be specified when running the agent. |

In typing terms, agents are generic in their dependency and output types, e.g., an agent which required dependencies of type `Foobar` and produced outputs of type `list[str]` would have type `Agent[Foobar, list[str]]`. In practice, you shouldn't need to care about this, it should just mean your IDE can tell you when you have the right type, and if you choose to use [static type checking](#static-type-checking) it should work well with Pydantic AI.

Here's a toy example of an agent that simulates a roulette wheel:

[Learn about Gateway](../gateway) roulette_wheel.py

```python
from pydantic_ai import Agent, RunContext

roulette_agent = Agent(  # (1)!
    'gateway/openai:gpt-5',
    deps_type=int,
    output_type=bool,
    system_prompt=(
        'Use the `roulette_wheel` function to see if the '
        'customer has won based on the number they provide.'
    ),
)


@roulette_agent.tool
async def roulette_wheel(ctx: RunContext[int], square: int) -> str:  # (2)!
    """check if the square is a winner"""
    return 'winner' if square == ctx.deps else 'loser'
