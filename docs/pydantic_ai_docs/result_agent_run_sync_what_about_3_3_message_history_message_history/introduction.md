```

#### Keep Only Recent Messages

You can use the `history_processor` to only keep the recent messages:

[Learn about Gateway](../gateway) keep_recent_messages.py

```python
from pydantic_ai import Agent, ModelMessage


async def keep_recent_messages(messages: list[ModelMessage]) -> list[ModelMessage]:
    """Keep only the last 5 messages to manage token usage."""
    return messages[-5:] if len(messages) > 5 else messages

agent = Agent('gateway/openai:gpt-5', history_processors=[keep_recent_messages])
