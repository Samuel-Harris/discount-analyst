## System Prompts

System prompts might seem simple at first glance since they're just strings (or sequences of strings that are concatenated), but crafting the right system prompt is key to getting the model to behave as you want.

Tip

For most use cases, you should use `instructions` instead of "system prompts".

If you know what you are doing though and want to preserve system prompt messages in the message history sent to the LLM in subsequent completions requests, you can achieve this using the `system_prompt` argument/decorator.

See the section below on [Instructions](#instructions) for more information.

Generally, system prompts fall into two categories:

1. **Static system prompts**: These are known when writing the code and can be defined via the `system_prompt` parameter of the Agent constructor.
1. **Dynamic system prompts**: These depend in some way on context that isn't known until runtime, and should be defined via functions decorated with @agent.system_prompt.

You can add both to a single agent; they're appended in the order they're defined at runtime.

Here's an example using both types of system prompts:

[Learn about Gateway](../gateway) system_prompts.py

```python
from datetime import date

from pydantic_ai import Agent, RunContext

agent = Agent(
    'gateway/openai:gpt-5',
    deps_type=str,  # (1)!
    system_prompt="Use the customer's name while replying to them.",  # (2)!
)


@agent.system_prompt  # (3)!
def add_the_users_name(ctx: RunContext[str]) -> str:
    return f"The user's name is {ctx.deps}."


@agent.system_prompt
def add_the_date() -> str:  # (4)!
    return f'The date is {date.today()}.'


result = agent.run_sync('What is the date?', deps='Frank')
print(result.output)
#> Hello Frank, the date today is 2032-01-02.

```

1. The agent expects a string dependency.
1. Static system prompt defined at agent creation time.
1. Dynamic system prompt defined via a decorator with RunContext, this is called just after `run_sync`, not when the agent is created, so can benefit from runtime information like the dependencies used on that run.
1. Another dynamic system prompt, system prompts don't have to have the `RunContext` parameter.

system_prompts.py

```python
from datetime import date

from pydantic_ai import Agent, RunContext

agent = Agent(
    'openai:gpt-5',
    deps_type=str,  # (1)!
    system_prompt="Use the customer's name while replying to them.",  # (2)!
)


@agent.system_prompt  # (3)!
def add_the_users_name(ctx: RunContext[str]) -> str:
    return f"The user's name is {ctx.deps}."


@agent.system_prompt
def add_the_date() -> str:  # (4)!
    return f'The date is {date.today()}.'


result = agent.run_sync('What is the date?', deps='Frank')
print(result.output)
#> Hello Frank, the date today is 2032-01-02.

```

1. The agent expects a string dependency.
1. Static system prompt defined at agent creation time.
1. Dynamic system prompt defined via a decorator with RunContext, this is called just after `run_sync`, not when the agent is created, so can benefit from runtime information like the dependencies used on that run.
1. Another dynamic system prompt, system prompts don't have to have the `RunContext` parameter.

_(This example is complete, it can be run "as is")_
