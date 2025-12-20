### Accessing Cache Usage Statistics

Access cache usage statistics via `result.usage()`:

[Learn about Gateway](../../gateway)

```python
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModelSettings

agent = Agent(
    'gateway/anthropic:claude-sonnet-4-5',
    system_prompt='Instructions...',
    model_settings=AnthropicModelSettings(
        anthropic_cache_instructions=True  # Default 5m TTL
    ),
)

result = agent.run_sync('Your question')
usage = result.usage()
print(f'Cache write tokens: {usage.cache_write_tokens}')
print(f'Cache read tokens: {usage.cache_read_tokens}')

```

```python
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModelSettings

agent = Agent(
    'anthropic:claude-sonnet-4-5',
    system_prompt='Instructions...',
    model_settings=AnthropicModelSettings(
        anthropic_cache_instructions=True  # Default 5m TTL
    ),
)

result = agent.run_sync('Your question')
usage = result.usage()
print(f'Cache write tokens: {usage.cache_write_tokens}')
print(f'Cache read tokens: {usage.cache_read_tokens}')

```
