## Hello World Example

Here's a minimal example of Pydantic AI:

[Learn about Gateway](../gateway) hello_world.py

```python
from pydantic_ai import Agent

agent = Agent(  # (1)!
    'gateway/anthropic:claude-sonnet-4-0',
    instructions='Be concise, reply with one sentence.',  # (2)!
)

result = agent.run_sync('Where does "hello world" come from?')  # (3)!
print(result.output)
"""
The first known use of "hello, world" was in a 1974 textbook about the C programming language.
"""

```

1. We configure the agent to use [Anthropic's Claude Sonnet 4.0](api/models/anthropic/) model, but you can also set the model when running the agent.
1. Register static [instructions](agents/#instructions) using a keyword argument to the agent.
1. [Run the agent](agents/#running-agents) synchronously, starting a conversation with the LLM.

hello_world.py

```python
from pydantic_ai import Agent

agent = Agent(  # (1)!
    'anthropic:claude-sonnet-4-0',
    instructions='Be concise, reply with one sentence.',  # (2)!
)

result = agent.run_sync('Where does "hello world" come from?')  # (3)!
print(result.output)
"""
The first known use of "hello, world" was in a 1974 textbook about the C programming language.
"""

```

1. We configure the agent to use [Anthropic's Claude Sonnet 4.0](api/models/anthropic/) model, but you can also set the model when running the agent.
1. Register static [instructions](agents/#instructions) using a keyword argument to the agent.
1. [Run the agent](agents/#running-agents) synchronously, starting a conversation with the LLM.

_(This example is complete, it can be run "as is", assuming you've [installed the `pydantic_ai` package](install/))_

The exchange will be very short: Pydantic AI will send the instructions and the user prompt to the LLM, and the model will return a text response.

Not very interesting yet, but we can easily add [tools](tools/), [dynamic instructions](agents/#instructions), and [structured outputs](output/) to build more powerful agents.
