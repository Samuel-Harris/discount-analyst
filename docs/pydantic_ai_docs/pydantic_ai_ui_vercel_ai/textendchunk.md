### TextEndChunk

Bases: `BaseChunk`

Text end chunk.

Source code in `pydantic_ai_slim/pydantic_ai/ui/vercel_ai/response_types.py`

```python
class TextEndChunk(BaseChunk):
    """Text end chunk."""

    type: Literal['text-end'] = 'text-end'
    id: str
    provider_metadata: ProviderMetadata | None = None

```
