### CachePoint

A cache point marker for prompt caching.

Can be inserted into UserPromptPart.content to mark cache boundaries. Models that don't support caching will filter these out.

Supported by:

- Anthropic

Source code in `pydantic_ai_slim/pydantic_ai/messages.py`

```python
@dataclass
class CachePoint:
    """A cache point marker for prompt caching.

    Can be inserted into UserPromptPart.content to mark cache boundaries.
    Models that don't support caching will filter these out.

    Supported by:

    - Anthropic
    """

    kind: Literal['cache-point'] = 'cache-point'
    """Type identifier, this is available on all parts as a discriminator."""

    ttl: Literal['5m', '1h'] = '5m'
    """The cache time-to-live, either "5m" (5 minutes) or "1h" (1 hour).

    Supported by:

    * Anthropic (automatically omitted for Bedrock, as it does not support explicit TTL). See https://docs.claude.com/en/docs/build-with-claude/prompt-caching#1-hour-cache-duration for more information."""

```

#### kind

```python
kind: Literal['cache-point'] = 'cache-point'

```

Type identifier, this is available on all parts as a discriminator.

#### ttl

```python
ttl: Literal['5m', '1h'] = '5m'

```

The cache time-to-live, either "5m" (5 minutes) or "1h" (1 hour).

Supported by:

- Anthropic (automatically omitted for Bedrock, as it does not support explicit TTL). See https://docs.claude.com/en/docs/build-with-claude/prompt-caching#1-hour-cache-duration for more information.
