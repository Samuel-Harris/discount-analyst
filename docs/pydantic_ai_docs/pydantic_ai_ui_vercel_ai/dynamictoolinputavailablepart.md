### DynamicToolInputAvailablePart

Bases: `BaseUIPart`

Dynamic tool part in input-available state.

Source code in `pydantic_ai_slim/pydantic_ai/ui/vercel_ai/request_types.py`

```python
class DynamicToolInputAvailablePart(BaseUIPart):
    """Dynamic tool part in input-available state."""

    type: Literal['dynamic-tool'] = 'dynamic-tool'
    tool_name: str
    tool_call_id: str
    state: Literal['input-available'] = 'input-available'
    input: Any
    call_provider_metadata: ProviderMetadata | None = None

```
