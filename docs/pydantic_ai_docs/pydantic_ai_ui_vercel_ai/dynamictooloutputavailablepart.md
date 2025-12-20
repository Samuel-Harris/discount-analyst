### DynamicToolOutputAvailablePart

Bases: `BaseUIPart`

Dynamic tool part in output-available state.

Source code in `pydantic_ai_slim/pydantic_ai/ui/vercel_ai/request_types.py`

```python
class DynamicToolOutputAvailablePart(BaseUIPart):
    """Dynamic tool part in output-available state."""

    type: Literal['dynamic-tool'] = 'dynamic-tool'
    tool_name: str
    tool_call_id: str
    state: Literal['output-available'] = 'output-available'
    input: Any
    output: Any
    call_provider_metadata: ProviderMetadata | None = None
    preliminary: bool | None = None

```
