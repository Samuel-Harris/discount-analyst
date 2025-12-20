### TextStartChunk

Bases: `BaseChunk`

Text start chunk.

Source code in `pydantic_ai_slim/pydantic_ai/ui/vercel_ai/response_types.py`

```python
class TextStartChunk(BaseChunk):
    """Text start chunk."""

    type: Literal['text-start'] = 'text-start'
    id: str
    provider_metadata: ProviderMetadata | None = None

```
