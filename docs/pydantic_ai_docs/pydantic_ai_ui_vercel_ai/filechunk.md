### FileChunk

Bases: `BaseChunk`

File chunk.

Source code in `pydantic_ai_slim/pydantic_ai/ui/vercel_ai/response_types.py`

```python
class FileChunk(BaseChunk):
    """File chunk."""

    type: Literal['file'] = 'file'
    url: str
    media_type: str

```
