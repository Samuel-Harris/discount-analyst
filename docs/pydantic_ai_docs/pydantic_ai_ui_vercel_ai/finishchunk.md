### FinishChunk

Bases: `BaseChunk`

Finish chunk.

Source code in `pydantic_ai_slim/pydantic_ai/ui/vercel_ai/response_types.py`

```python
class FinishChunk(BaseChunk):
    """Finish chunk."""

    type: Literal['finish'] = 'finish'
    message_metadata: Any | None = None

```
