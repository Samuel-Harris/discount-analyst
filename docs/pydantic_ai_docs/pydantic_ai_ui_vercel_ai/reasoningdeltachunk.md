### ReasoningDeltaChunk

Bases: `BaseChunk`

Reasoning delta chunk.

Source code in `pydantic_ai_slim/pydantic_ai/ui/vercel_ai/response_types.py`

```python
class ReasoningDeltaChunk(BaseChunk):
    """Reasoning delta chunk."""

    type: Literal['reasoning-delta'] = 'reasoning-delta'
    id: str
    delta: str
    provider_metadata: ProviderMetadata | None = None

```
