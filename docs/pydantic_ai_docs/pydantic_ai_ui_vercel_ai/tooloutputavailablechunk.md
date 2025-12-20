### ToolOutputAvailableChunk

Bases: `BaseChunk`

Tool output available chunk.

Source code in `pydantic_ai_slim/pydantic_ai/ui/vercel_ai/response_types.py`

```python
class ToolOutputAvailableChunk(BaseChunk):
    """Tool output available chunk."""

    type: Literal['tool-output-available'] = 'tool-output-available'
    tool_call_id: str
    output: Any
    provider_executed: bool | None = None
    dynamic: bool | None = None
    preliminary: bool | None = None

```
