### ToolInputErrorChunk

Bases: `BaseChunk`

Tool input error chunk.

Source code in `pydantic_ai_slim/pydantic_ai/ui/vercel_ai/response_types.py`

```python
class ToolInputErrorChunk(BaseChunk):
    """Tool input error chunk."""

    type: Literal['tool-input-error'] = 'tool-input-error'
    tool_call_id: str
    tool_name: str
    input: Any
    provider_executed: bool | None = None
    provider_metadata: ProviderMetadata | None = None
    dynamic: bool | None = None
    error_text: str

```
