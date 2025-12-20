result = agent.run_sync([
    'Context', CachePoint(),  # 4th cache point - OK
    'Question'
])
print(result.output)
usage = result.usage()
print(f'Cache write tokens: {usage.cache_write_tokens}')
print(f'Cache read tokens: {usage.cache_read_tokens}')

```

#### Automatic Cache Point Limiting

When cache points from all sources (settings + `CachePoint` markers) exceed 4, Pydantic AI automatically removes excess cache points from **older message content** (keeping the most recent ones).

Define an agent with 2 cache points from settings:

[Learn about Gateway](../../gateway)

```python
from pydantic_ai import Agent, CachePoint
from pydantic_ai.models.anthropic import AnthropicModelSettings

agent = Agent(
    'gateway/anthropic:claude-sonnet-4-5',
    system_prompt='Instructions...',
    model_settings=AnthropicModelSettings(
        anthropic_cache_instructions=True,      # 1 cache point
        anthropic_cache_tool_definitions=True,  # 1 cache point
    ),
)

@agent.tool_plain
def search() -> str:
    return 'data'
