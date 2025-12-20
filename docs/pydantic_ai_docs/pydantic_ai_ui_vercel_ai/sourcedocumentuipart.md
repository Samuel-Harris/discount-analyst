### SourceDocumentUIPart

Bases: `BaseUIPart`

A document source part of a message.

Source code in `pydantic_ai_slim/pydantic_ai/ui/vercel_ai/request_types.py`

```python
class SourceDocumentUIPart(BaseUIPart):
    """A document source part of a message."""

    type: Literal['source-document'] = 'source-document'
    source_id: str
    media_type: str
    title: str
    filename: str | None = None
    provider_metadata: ProviderMetadata | None = None

```
