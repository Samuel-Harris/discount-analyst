### Example 1: Automatic Message Caching

Use `anthropic_cache_messages` to automatically cache all messages up to and including the newest user message:

[Learn about Gateway](../../gateway)

```python
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModelSettings

agent = Agent(
    'gateway/anthropic:claude-sonnet-4-5',
    system_prompt='You are a helpful assistant.',
    model_settings=AnthropicModelSettings(
        anthropic_cache_messages=True,  # Automatically caches the last message
    ),
)
