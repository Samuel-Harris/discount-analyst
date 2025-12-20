### SourceUrlUIPart

Bases: `BaseUIPart`

A source part of a message.

Source code in `pydantic_ai_slim/pydantic_ai/ui/vercel_ai/request_types.py`

```python
class SourceUrlUIPart(BaseUIPart):
    """A source part of a message."""

    type: Literal['source-url'] = 'source-url'
    source_id: str
    url: str
    title: str | None = None
    provider_metadata: ProviderMetadata | None = None

```
