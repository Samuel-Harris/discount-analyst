### AbortChunk

Bases: `BaseChunk`

Abort chunk.

Source code in `pydantic_ai_slim/pydantic_ai/ui/vercel_ai/response_types.py`

```python
class AbortChunk(BaseChunk):
    """Abort chunk."""

    type: Literal['abort'] = 'abort'

```
