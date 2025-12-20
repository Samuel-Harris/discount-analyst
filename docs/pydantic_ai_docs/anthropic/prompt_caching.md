## Prompt Caching

Anthropic supports [prompt caching](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching) to reduce costs by caching parts of your prompts. Pydantic AI provides four ways to use prompt caching:

1. **Cache User Messages with CachePoint**: Insert a `CachePoint` marker in your user messages to cache everything before it
1. **Cache System Instructions**: Set AnthropicModelSettings.anthropic_cache_instructions to `True` (uses 5m TTL by default) or specify `'5m'` / `'1h'` directly
1. **Cache Tool Definitions**: Set AnthropicModelSettings.anthropic_cache_tool_definitions to `True` (uses 5m TTL by default) or specify `'5m'` / `'1h'` directly
1. **Cache All Messages**: Set AnthropicModelSettings.anthropic_cache_messages to `True` to automatically cache all messages

Amazon Bedrock

When using `AsyncAnthropicBedrock`, the TTL parameter is automatically omitted from all cache control settings (including `CachePoint`, `anthropic_cache_instructions`, `anthropic_cache_tool_definitions`, and `anthropic_cache_messages`) because Bedrock doesn't support explicit TTL.
