```

Be careful when slicing the message history

When slicing the message history, you need to make sure that tool calls and returns are paired, otherwise the LLM may return an error. For more details, refer to [this GitHub issue](https://github.com/pydantic/pydantic-ai/issues/2050#issuecomment-3019976269).

#### `RunContext` parameter

History processors can optionally accept a RunContext parameter to access additional information about the current run, such as dependencies, model information, and usage statistics:

[Learn about Gateway](../gateway) context_aware_processor.py

```python
from pydantic_ai import Agent, ModelMessage, RunContext


def context_aware_processor(
    ctx: RunContext[None],
    messages: list[ModelMessage],
) -> list[ModelMessage]:
    # Access current usage
    current_tokens = ctx.usage.total_tokens

    # Filter messages based on context
    if current_tokens > 1000:
        return messages[-3:]  # Keep only recent messages when token usage is high
    return messages

agent = Agent('gateway/openai:gpt-5', history_processors=[context_aware_processor])

```

context_aware_processor.py

```python
from pydantic_ai import Agent, ModelMessage, RunContext


def context_aware_processor(
    ctx: RunContext[None],
    messages: list[ModelMessage],
) -> list[ModelMessage]:
    # Access current usage
    current_tokens = ctx.usage.total_tokens

    # Filter messages based on context
    if current_tokens > 1000:
        return messages[-3:]  # Keep only recent messages when token usage is high
    return messages

agent = Agent('openai:gpt-5', history_processors=[context_aware_processor])

```

This allows for more sophisticated message processing based on the current state of the agent run.

#### Summarize Old Messages

Use an LLM to summarize older messages to preserve context while reducing tokens.

[Learn about Gateway](../gateway) summarize_old_messages.py

```python
from pydantic_ai import Agent, ModelMessage
