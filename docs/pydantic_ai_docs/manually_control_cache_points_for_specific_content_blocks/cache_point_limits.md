### Cache Point Limits

Anthropic enforces a maximum of 4 cache points per request. Pydantic AI automatically manages this limit to ensure your requests always comply without errors.

#### How Cache Points Are Allocated

Cache points can be placed in three locations:

1. **System Prompt**: Via `anthropic_cache_instructions` setting (adds cache point to last system prompt block)
1. **Tool Definitions**: Via `anthropic_cache_tool_definitions` setting (adds cache point to last tool definition)
1. **Messages**: Via `CachePoint` markers or `anthropic_cache_messages` setting (adds cache points to message content)

Each setting uses **at most 1 cache point**, but you can combine them.

#### Example: Using All 3 Cache Point Sources

Define an agent with all cache settings enabled:

[Learn about Gateway](../../gateway)

```python
from pydantic_ai import Agent, CachePoint
from pydantic_ai.models.anthropic import AnthropicModelSettings

agent = Agent(
    'gateway/anthropic:claude-sonnet-4-5',
    system_prompt='Detailed instructions...',
    model_settings=AnthropicModelSettings(
        anthropic_cache_instructions=True,      # 1 cache point
        anthropic_cache_tool_definitions=True,  # 1 cache point
        anthropic_cache_messages=True,          # 1 cache point
    ),
)

@agent.tool_plain
def my_tool() -> str:
    return 'result'
