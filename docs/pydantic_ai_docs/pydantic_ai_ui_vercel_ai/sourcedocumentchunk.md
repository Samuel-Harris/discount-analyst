### SourceDocumentChunk

Bases: `BaseChunk`

Source document chunk.

Source code in `pydantic_ai_slim/pydantic_ai/ui/vercel_ai/response_types.py`

```python
class SourceDocumentChunk(BaseChunk):
    """Source document chunk."""

    type: Literal['source-document'] = 'source-document'
    source_id: str
    media_type: str
    title: str
    filename: str | None = None
    provider_metadata: ProviderMetadata | None = None

```
