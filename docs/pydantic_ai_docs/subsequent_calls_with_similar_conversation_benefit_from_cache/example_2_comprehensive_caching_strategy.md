### Example 2: Comprehensive Caching Strategy

Combine multiple cache settings for maximum savings:

[Learn about Gateway](../../gateway)

```python
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.anthropic import AnthropicModelSettings

agent = Agent(
    'gateway/anthropic:claude-sonnet-4-5',
    system_prompt='Detailed instructions...',
    model_settings=AnthropicModelSettings(
        anthropic_cache_instructions=True,      # Cache system instructions
        anthropic_cache_tool_definitions='1h',  # Cache tool definitions with 1h TTL
        anthropic_cache_messages=True,          # Also cache the last message
    ),
)

@agent.tool
def search_docs(ctx: RunContext, query: str) -> str:
    """Search documentation."""
    return f'Results for {query}'


result = agent.run_sync('Search for Python best practices')
print(result.output)

```

```python
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.anthropic import AnthropicModelSettings

agent = Agent(
    'anthropic:claude-sonnet-4-5',
    system_prompt='Detailed instructions...',
    model_settings=AnthropicModelSettings(
        anthropic_cache_instructions=True,      # Cache system instructions
        anthropic_cache_tool_definitions='1h',  # Cache tool definitions with 1h TTL
        anthropic_cache_messages=True,          # Also cache the last message
    ),
)

@agent.tool
def search_docs(ctx: RunContext, query: str) -> str:
    """Search documentation."""
    return f'Results for {query}'


result = agent.run_sync('Search for Python best practices')
print(result.output)

```
