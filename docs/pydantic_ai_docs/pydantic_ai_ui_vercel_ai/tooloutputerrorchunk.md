### ToolOutputErrorChunk

Bases: `BaseChunk`

Tool output error chunk.

Source code in `pydantic_ai_slim/pydantic_ai/ui/vercel_ai/response_types.py`

```python
class ToolOutputErrorChunk(BaseChunk):
    """Tool output error chunk."""

    type: Literal['tool-output-error'] = 'tool-output-error'
    tool_call_id: str
    error_text: str
    provider_executed: bool | None = None
    dynamic: bool | None = None

```
