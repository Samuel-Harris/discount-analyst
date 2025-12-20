### ToolInputStartChunk

Bases: `BaseChunk`

Tool input start chunk.

Source code in `pydantic_ai_slim/pydantic_ai/ui/vercel_ai/response_types.py`

```python
class ToolInputStartChunk(BaseChunk):
    """Tool input start chunk."""

    type: Literal['tool-input-start'] = 'tool-input-start'
    tool_call_id: str
    tool_name: str
    provider_executed: bool | None = None
    dynamic: bool | None = None

```
