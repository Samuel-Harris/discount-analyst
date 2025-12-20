### UrlContextTool

Bases: `WebFetchTool`

Deprecated

Use `WebFetchTool` instead.

Deprecated alias for WebFetchTool. Use WebFetchTool instead.

Overrides kind to 'url_context' so old serialized payloads with {"kind": "url_context", ...} can be deserialized to UrlContextTool for backward compatibility.

Source code in `pydantic_ai_slim/pydantic_ai/builtin_tools.py`

```python
@deprecated('Use `WebFetchTool` instead.')
@dataclass(kw_only=True)
class UrlContextTool(WebFetchTool):
    """Deprecated alias for WebFetchTool. Use WebFetchTool instead.

    Overrides kind to 'url_context' so old serialized payloads with {"kind": "url_context", ...}
    can be deserialized to UrlContextTool for backward compatibility.
    """

    kind: str = 'url_context'
    """The kind of tool (deprecated value for backward compatibility)."""

```

#### kind

```python
kind: str = 'url_context'

```

The kind of tool (deprecated value for backward compatibility).
