### ToolInputStreamingPart

Bases: `BaseUIPart`

Tool part in input-streaming state.

Source code in `pydantic_ai_slim/pydantic_ai/ui/vercel_ai/request_types.py`

```python
class ToolInputStreamingPart(BaseUIPart):
    """Tool part in input-streaming state."""

    type: Annotated[str, Field(pattern=r'^tool-')]
    tool_call_id: str
    state: Literal['input-streaming'] = 'input-streaming'
    input: Any | None = None
    provider_executed: bool | None = None

```
