### Multiple Processors

You can also use multiple processors:

[Learn about Gateway](../gateway) multiple_history_processors.py

```python
from pydantic_ai import Agent, ModelMessage, ModelRequest


def filter_responses(messages: list[ModelMessage]) -> list[ModelMessage]:
    return [msg for msg in messages if isinstance(msg, ModelRequest)]


def summarize_old_messages(messages: list[ModelMessage]) -> list[ModelMessage]:
    return messages[-5:]


agent = Agent('gateway/openai:gpt-5', history_processors=[filter_responses, summarize_old_messages])

```

multiple_history_processors.py

```python
from pydantic_ai import Agent, ModelMessage, ModelRequest


def filter_responses(messages: list[ModelMessage]) -> list[ModelMessage]:
    return [msg for msg in messages if isinstance(msg, ModelRequest)]


def summarize_old_messages(messages: list[ModelMessage]) -> list[ModelMessage]:
    return messages[-5:]


agent = Agent('openai:gpt-5', history_processors=[filter_responses, summarize_old_messages])

```

In this case, the `filter_responses` processor will be applied first, and the `summarize_old_messages` processor will be applied second.
