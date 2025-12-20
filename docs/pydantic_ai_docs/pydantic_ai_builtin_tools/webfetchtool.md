### WebFetchTool

Bases: `AbstractBuiltinTool`

Allows your agent to access contents from URLs.

The parameters that PydanticAI passes depend on the model, as some parameters may not be supported by certain models.

Supported by:

- Anthropic
- Google

Source code in `pydantic_ai_slim/pydantic_ai/builtin_tools.py`

```python
@dataclass(kw_only=True)
class WebFetchTool(AbstractBuiltinTool):
    """Allows your agent to access contents from URLs.

    The parameters that PydanticAI passes depend on the model, as some parameters may not be supported by certain models.

    Supported by:

    * Anthropic
    * Google
    """

    max_uses: int | None = None
    """If provided, the tool will stop fetching URLs after the given number of uses.

    Supported by:

    * Anthropic
    """

    allowed_domains: list[str] | None = None
    """If provided, only these domains will be fetched.

    With Anthropic, you can only use one of `blocked_domains` or `allowed_domains`, not both.

    Supported by:

    * Anthropic, see <https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/web-fetch-tool#domain-filtering>
    """

    blocked_domains: list[str] | None = None
    """If provided, these domains will never be fetched.

    With Anthropic, you can only use one of `blocked_domains` or `allowed_domains`, not both.

    Supported by:

    * Anthropic, see <https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/web-fetch-tool#domain-filtering>
    """

    enable_citations: bool = False
    """If True, enables citations for fetched content.

    Supported by:

    * Anthropic
    """

    max_content_tokens: int | None = None
    """Maximum content length in tokens for fetched content.

    Supported by:

    * Anthropic
    """

    kind: str = 'web_fetch'
    """The kind of tool."""

```

#### max_uses

```python
max_uses: int | None = None

```

If provided, the tool will stop fetching URLs after the given number of uses.

Supported by:

- Anthropic

#### allowed_domains

```python
allowed_domains: list[str] | None = None

```

If provided, only these domains will be fetched.

With Anthropic, you can only use one of `blocked_domains` or `allowed_domains`, not both.

Supported by:

- Anthropic, see <https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/web-fetch-tool#domain-filtering>

#### blocked_domains

```python
blocked_domains: list[str] | None = None

```

If provided, these domains will never be fetched.

With Anthropic, you can only use one of `blocked_domains` or `allowed_domains`, not both.

Supported by:

- Anthropic, see <https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/web-fetch-tool#domain-filtering>

#### enable_citations

```python
enable_citations: bool = False

```

If True, enables citations for fetched content.

Supported by:

- Anthropic

#### max_content_tokens

```python
max_content_tokens: int | None = None

```

Maximum content length in tokens for fetched content.

Supported by:

- Anthropic

#### kind

```python
kind: str = 'web_fetch'

```

The kind of tool.
