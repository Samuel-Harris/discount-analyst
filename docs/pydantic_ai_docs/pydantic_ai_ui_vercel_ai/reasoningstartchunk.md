### ReasoningStartChunk

Bases: `BaseChunk`

Reasoning start chunk.

Source code in `pydantic_ai_slim/pydantic_ai/ui/vercel_ai/response_types.py`

```python
class ReasoningStartChunk(BaseChunk):
    """Reasoning start chunk."""

    type: Literal['reasoning-start'] = 'reasoning-start'
    id: str
    provider_metadata: ProviderMetadata | None = None

```
