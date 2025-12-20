### SourceUrlChunk

Bases: `BaseChunk`

Source URL chunk.

Source code in `pydantic_ai_slim/pydantic_ai/ui/vercel_ai/response_types.py`

```python
class SourceUrlChunk(BaseChunk):
    """Source URL chunk."""

    type: Literal['source-url'] = 'source-url'
    source_id: str
    url: str
    title: str | None = None
    provider_metadata: ProviderMetadata | None = None

```
