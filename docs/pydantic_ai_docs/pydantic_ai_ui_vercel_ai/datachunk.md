### DataChunk

Bases: `BaseChunk`

Data chunk with dynamic type.

Source code in `pydantic_ai_slim/pydantic_ai/ui/vercel_ai/response_types.py`

```python
class DataChunk(BaseChunk):
    """Data chunk with dynamic type."""

    type: Annotated[str, Field(pattern=r'^data-')]
    data: Any

```
