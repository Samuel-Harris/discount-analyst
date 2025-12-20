### DynamicToolOutputErrorPart

Bases: `BaseUIPart`

Dynamic tool part in output-error state.

Source code in `pydantic_ai_slim/pydantic_ai/ui/vercel_ai/request_types.py`

```python
class DynamicToolOutputErrorPart(BaseUIPart):
    """Dynamic tool part in output-error state."""

    type: Literal['dynamic-tool'] = 'dynamic-tool'
    tool_name: str
    tool_call_id: str
    state: Literal['output-error'] = 'output-error'
    input: Any
    error_text: str
    call_provider_metadata: ProviderMetadata | None = None

```
