### ToolInputAvailableChunk

Bases: `BaseChunk`

Tool input available chunk.

Source code in `pydantic_ai_slim/pydantic_ai/ui/vercel_ai/response_types.py`

```python
class ToolInputAvailableChunk(BaseChunk):
    """Tool input available chunk."""

    type: Literal['tool-input-available'] = 'tool-input-available'
    tool_call_id: str
    tool_name: str
    input: Any
    provider_executed: bool | None = None
    provider_metadata: ProviderMetadata | None = None
    dynamic: bool | None = None

```
