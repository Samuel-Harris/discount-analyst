### WebSearchTool

Bases: `AbstractBuiltinTool`

A builtin tool that allows your agent to search the web for information.

The parameters that PydanticAI passes depend on the model, as some parameters may not be supported by certain models.

Supported by:

- Anthropic
- OpenAI Responses
- Groq
- Google

Source code in `pydantic_ai_slim/pydantic_ai/builtin_tools.py`

```python
@dataclass(kw_only=True)
class WebSearchTool(AbstractBuiltinTool):
    """A builtin tool that allows your agent to search the web for information.

    The parameters that PydanticAI passes depend on the model, as some parameters may not be supported by certain models.

    Supported by:

    * Anthropic
    * OpenAI Responses
    * Groq
    * Google
    """

    search_context_size: Literal['low', 'medium', 'high'] = 'medium'
    """The `search_context_size` parameter controls how much context is retrieved from the web to help the tool formulate a response.

    Supported by:

    * OpenAI Responses
    """

    user_location: WebSearchUserLocation | None = None
    """The `user_location` parameter allows you to localize search results based on a user's location.

    Supported by:

    * Anthropic
    * OpenAI Responses
    """

    blocked_domains: list[str] | None = None
    """If provided, these domains will never appear in results.

    With Anthropic, you can only use one of `blocked_domains` or `allowed_domains`, not both.

    Supported by:

    * Anthropic, see <https://docs.anthropic.com/en/docs/build-with-claude/tool-use/web-search-tool#domain-filtering>
    * Groq, see <https://console.groq.com/docs/agentic-tooling#search-settings>
    """

    allowed_domains: list[str] | None = None
    """If provided, only these domains will be included in results.

    With Anthropic, you can only use one of `blocked_domains` or `allowed_domains`, not both.

    Supported by:

    * Anthropic, see <https://docs.anthropic.com/en/docs/build-with-claude/tool-use/web-search-tool#domain-filtering>
    * Groq, see <https://console.groq.com/docs/agentic-tooling#search-settings>
    """

    max_uses: int | None = None
    """If provided, the tool will stop searching the web after the given number of uses.

    Supported by:

    * Anthropic
    """

    kind: str = 'web_search'
    """The kind of tool."""

```

#### search_context_size

```python
search_context_size: Literal["low", "medium", "high"] = (
    "medium"
)

```

The `search_context_size` parameter controls how much context is retrieved from the web to help the tool formulate a response.

Supported by:

- OpenAI Responses

#### user_location

```python
user_location: WebSearchUserLocation | None = None

```

The `user_location` parameter allows you to localize search results based on a user's location.

Supported by:

- Anthropic
- OpenAI Responses

#### blocked_domains

```python
blocked_domains: list[str] | None = None

```

If provided, these domains will never appear in results.

With Anthropic, you can only use one of `blocked_domains` or `allowed_domains`, not both.

Supported by:

- Anthropic, see <https://docs.anthropic.com/en/docs/build-with-claude/tool-use/web-search-tool#domain-filtering>
- Groq, see <https://console.groq.com/docs/agentic-tooling#search-settings>

#### allowed_domains

```python
allowed_domains: list[str] | None = None

```

If provided, only these domains will be included in results.

With Anthropic, you can only use one of `blocked_domains` or `allowed_domains`, not both.

Supported by:

- Anthropic, see <https://docs.anthropic.com/en/docs/build-with-claude/tool-use/web-search-tool#domain-filtering>
- Groq, see <https://console.groq.com/docs/agentic-tooling#search-settings>

#### max_uses

```python
max_uses: int | None = None

```

If provided, the tool will stop searching the web after the given number of uses.

Supported by:

- Anthropic

#### kind

```python
kind: str = 'web_search'

```

The kind of tool.
