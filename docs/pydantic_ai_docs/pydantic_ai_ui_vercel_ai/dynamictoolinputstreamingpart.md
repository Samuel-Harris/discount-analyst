### DynamicToolInputStreamingPart

Bases: `BaseUIPart`

Dynamic tool part in input-streaming state.

Source code in `pydantic_ai_slim/pydantic_ai/ui/vercel_ai/request_types.py`

```python
class DynamicToolInputStreamingPart(BaseUIPart):
    """Dynamic tool part in input-streaming state."""

    type: Literal['dynamic-tool'] = 'dynamic-tool'
    tool_name: str
    tool_call_id: str
    state: Literal['input-streaming'] = 'input-streaming'
    input: Any | None = None

```
