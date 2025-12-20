### ErrorChunk

Bases: `BaseChunk`

Error chunk.

Source code in `pydantic_ai_slim/pydantic_ai/ui/vercel_ai/response_types.py`

```python
class ErrorChunk(BaseChunk):
    """Error chunk."""

    type: Literal['error'] = 'error'
    error_text: str

```
