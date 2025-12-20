### AnthropicModelSettings

Bases: `ModelSettings`

Settings used for an Anthropic model request.

Source code in `pydantic_ai_slim/pydantic_ai/models/anthropic.py`

```python
class AnthropicModelSettings(ModelSettings, total=False):
    """Settings used for an Anthropic model request."""

    # ALL FIELDS MUST BE `anthropic_` PREFIXED SO YOU CAN MERGE THEM WITH OTHER MODELS.

    anthropic_metadata: BetaMetadataParam
    """An object describing metadata about the request.

    Contains `user_id`, an external identifier for the user who is associated with the request.
    """

    anthropic_thinking: BetaThinkingConfigParam
    """Determine whether the model should generate a thinking block.

    See [the Anthropic docs](https://docs.anthropic.com/en/docs/build-with-claude/extended-thinking) for more information.
    """

    anthropic_cache_tool_definitions: bool | Literal['5m', '1h']
    """Whether to add `cache_control` to the last tool definition.

    When enabled, the last tool in the `tools` array will have `cache_control` set,
    allowing Anthropic to cache tool definitions and reduce costs.
    If `True`, uses TTL='5m'. You can also specify '5m' or '1h' directly.
    TTL is automatically omitted for Bedrock, as it does not support explicit TTL.
    See https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching for more information.
    """

    anthropic_cache_instructions: bool | Literal['5m', '1h']
    """Whether to add `cache_control` to the last system prompt block.

    When enabled, the last system prompt will have `cache_control` set,
    allowing Anthropic to cache system instructions and reduce costs.
    If `True`, uses TTL='5m'. You can also specify '5m' or '1h' directly.
    TTL is automatically omitted for Bedrock, as it does not support explicit TTL.
    See https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching for more information.
    """

    anthropic_cache_messages: bool | Literal['5m', '1h']
    """Convenience setting to enable caching for the last user message.

    When enabled, this automatically adds a cache point to the last content block
    in the final user message, which is useful for caching conversation history
    or context in multi-turn conversations.
    If `True`, uses TTL='5m'. You can also specify '5m' or '1h' directly.
    TTL is automatically omitted for Bedrock, as it does not support explicit TTL.

    Note: Uses 1 of Anthropic's 4 available cache points per request. Any additional CachePoint
    markers in messages will be automatically limited to respect the 4-cache-point maximum.
    See https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching for more information.
    """

```

#### anthropic_metadata

```python
anthropic_metadata: BetaMetadataParam

```

An object describing metadata about the request.

Contains `user_id`, an external identifier for the user who is associated with the request.

#### anthropic_thinking

```python
anthropic_thinking: BetaThinkingConfigParam

```

Determine whether the model should generate a thinking block.

See [the Anthropic docs](https://docs.anthropic.com/en/docs/build-with-claude/extended-thinking) for more information.

#### anthropic_cache_tool_definitions

```python
anthropic_cache_tool_definitions: bool | Literal["5m", "1h"]

```

Whether to add `cache_control` to the last tool definition.

When enabled, the last tool in the `tools` array will have `cache_control` set, allowing Anthropic to cache tool definitions and reduce costs. If `True`, uses TTL='5m'. You can also specify '5m' or '1h' directly. TTL is automatically omitted for Bedrock, as it does not support explicit TTL. See https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching for more information.

#### anthropic_cache_instructions

```python
anthropic_cache_instructions: bool | Literal['5m', '1h']

```

Whether to add `cache_control` to the last system prompt block.

When enabled, the last system prompt will have `cache_control` set, allowing Anthropic to cache system instructions and reduce costs. If `True`, uses TTL='5m'. You can also specify '5m' or '1h' directly. TTL is automatically omitted for Bedrock, as it does not support explicit TTL. See https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching for more information.

#### anthropic_cache_messages

```python
anthropic_cache_messages: bool | Literal['5m', '1h']

```

Convenience setting to enable caching for the last user message.

When enabled, this automatically adds a cache point to the last content block in the final user message, which is useful for caching conversation history or context in multi-turn conversations. If `True`, uses TTL='5m'. You can also specify '5m' or '1h' directly. TTL is automatically omitted for Bedrock, as it does not support explicit TTL.

Note: Uses 1 of Anthropic's 4 available cache points per request. Any additional CachePoint markers in messages will be automatically limited to respect the 4-cache-point maximum. See https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching for more information.
