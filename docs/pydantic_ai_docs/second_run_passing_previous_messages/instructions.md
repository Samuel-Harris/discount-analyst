## Instructions

Instructions are similar to system prompts. The main difference is that when an explicit `message_history` is provided in a call to `Agent.run` and similar methods, _instructions_ from any existing messages in the history are not included in the request to the model â€” only the instructions of the _current_ agent are included.

You should use:

- `instructions` when you want your request to the model to only include system prompts for the _current_ agent
- `system_prompt` when you want your request to the model to _retain_ the system prompts used in previous requests (possibly made using other agents)

In general, we recommend using `instructions` instead of `system_prompt` unless you have a specific reason to use `system_prompt`.

Instructions, like system prompts, can be specified at different times:

1. **Static instructions**: These are known when writing the code and can be defined via the `instructions` parameter of the Agent constructor.
1. **Dynamic instructions**: These rely on context that is only available at runtime and should be defined using functions decorated with @agent.instructions. Unlike dynamic system prompts, which may be reused when `message_history` is present, dynamic instructions are always reevaluated.
1. \*_Runtime instructions_: These are additional instructions for a specific run that can be passed to one of the [run methods](#running-agents) using the `instructions` argument.

All three types of instructions can be added to a single agent, and they are appended in the order they are defined at runtime.

Here's an example using a static instruction as well as dynamic instructions:

[Learn about Gateway](../gateway) instructions.py

```python
from datetime import date

from pydantic_ai import Agent, RunContext

agent = Agent(
    'gateway/openai:gpt-5',
    deps_type=str,  # (1)!
    instructions="Use the customer's name while replying to them.",  # (2)!
)


@agent.instructions  # (3)!
def add_the_users_name(ctx: RunContext[str]) -> str:
    return f"The user's name is {ctx.deps}."


@agent.instructions
def add_the_date() -> str:  # (4)!
    return f'The date is {date.today()}.'


result = agent.run_sync('What is the date?', deps='Frank')
print(result.output)
#> Hello Frank, the date today is 2032-01-02.

```

1. The agent expects a string dependency.
1. Static instructions defined at agent creation time.
1. Dynamic instructions defined via a decorator with RunContext, this is called just after `run_sync`, not when the agent is created, so can benefit from runtime information like the dependencies used on that run.
1. Another dynamic instruction, instructions don't have to have the `RunContext` parameter.

instructions.py

```python
from datetime import date

from pydantic_ai import Agent, RunContext

agent = Agent(
    'openai:gpt-5',
    deps_type=str,  # (1)!
    instructions="Use the customer's name while replying to them.",  # (2)!
)


@agent.instructions  # (3)!
def add_the_users_name(ctx: RunContext[str]) -> str:
    return f"The user's name is {ctx.deps}."


@agent.instructions
def add_the_date() -> str:  # (4)!
    return f'The date is {date.today()}.'


result = agent.run_sync('What is the date?', deps='Frank')
print(result.output)
#> Hello Frank, the date today is 2032-01-02.

```

1. The agent expects a string dependency.
1. Static instructions defined at agent creation time.
1. Dynamic instructions defined via a decorator with RunContext, this is called just after `run_sync`, not when the agent is created, so can benefit from runtime information like the dependencies used on that run.
1. Another dynamic instruction, instructions don't have to have the `RunContext` parameter.

_(This example is complete, it can be run "as is")_

Note that returning an empty string will result in no instruction message added.
