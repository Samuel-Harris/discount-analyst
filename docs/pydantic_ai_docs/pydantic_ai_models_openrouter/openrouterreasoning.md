### OpenRouterReasoning

Bases: `TypedDict`

Configuration for reasoning tokens in OpenRouter requests.

Reasoning tokens allow models to show their step-by-step thinking process. You can configure this using either OpenAI-style effort levels or Anthropic-style token limits, but not both simultaneously.

Source code in `pydantic_ai_slim/pydantic_ai/models/openrouter.py`

```python
class OpenRouterReasoning(TypedDict, total=False):
    """Configuration for reasoning tokens in OpenRouter requests.

    Reasoning tokens allow models to show their step-by-step thinking process.
    You can configure this using either OpenAI-style effort levels or Anthropic-style
    token limits, but not both simultaneously.
    """

    effort: Literal['high', 'medium', 'low']
    """OpenAI-style reasoning effort level. Cannot be used with max_tokens."""

    max_tokens: int
    """Anthropic-style specific token limit for reasoning. Cannot be used with effort."""

    exclude: bool
    """Whether to exclude reasoning tokens from the response. Default is False. All models support this."""

    enabled: bool
    """Whether to enable reasoning with default parameters. Default is inferred from effort or max_tokens."""

```

#### effort

```python
effort: Literal['high', 'medium', 'low']

```

OpenAI-style reasoning effort level. Cannot be used with max_tokens.

#### max_tokens

```python
max_tokens: int

```

Anthropic-style specific token limit for reasoning. Cannot be used with effort.

#### exclude

```python
exclude: bool

```

Whether to exclude reasoning tokens from the response. Default is False. All models support this.

#### enabled

```python
enabled: bool

```

Whether to enable reasoning with default parameters. Default is inferred from effort or max_tokens.
