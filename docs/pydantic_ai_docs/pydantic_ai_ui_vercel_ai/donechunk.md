### DoneChunk

Bases: `BaseChunk`

Done chunk.

Source code in `pydantic_ai_slim/pydantic_ai/ui/vercel_ai/response_types.py`

```python
class DoneChunk(BaseChunk):
    """Done chunk."""

    type: Literal['done'] = 'done'

    def encode(self) -> str:
        return '[DONE]'

```
