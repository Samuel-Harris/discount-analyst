### ToolInputDeltaChunk

Bases: `BaseChunk`

Tool input delta chunk.

Source code in `pydantic_ai_slim/pydantic_ai/ui/vercel_ai/response_types.py`

```python
class ToolInputDeltaChunk(BaseChunk):
    """Tool input delta chunk."""

    type: Literal['tool-input-delta'] = 'tool-input-delta'
    tool_call_id: str
    input_text_delta: str

```
