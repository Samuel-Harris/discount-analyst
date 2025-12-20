### TextDeltaChunk

Bases: `BaseChunk`

Text delta chunk.

Source code in `pydantic_ai_slim/pydantic_ai/ui/vercel_ai/response_types.py`

```python
class TextDeltaChunk(BaseChunk):
    """Text delta chunk."""

    type: Literal['text-delta'] = 'text-delta'
    delta: str
    id: str
    provider_metadata: ProviderMetadata | None = None

```
