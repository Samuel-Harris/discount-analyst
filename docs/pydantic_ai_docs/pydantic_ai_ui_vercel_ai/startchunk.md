### StartChunk

Bases: `BaseChunk`

Start chunk.

Source code in `pydantic_ai_slim/pydantic_ai/ui/vercel_ai/response_types.py`

```python
class StartChunk(BaseChunk):
    """Start chunk."""

    type: Literal['start'] = 'start'
    message_id: str | None = None
    message_metadata: Any | None = None

```
