### ReasoningEndChunk

Bases: `BaseChunk`

Reasoning end chunk.

Source code in `pydantic_ai_slim/pydantic_ai/ui/vercel_ai/response_types.py`

```python
class ReasoningEndChunk(BaseChunk):
    """Reasoning end chunk."""

    type: Literal['reasoning-end'] = 'reasoning-end'
    id: str
    provider_metadata: ProviderMetadata | None = None

```
