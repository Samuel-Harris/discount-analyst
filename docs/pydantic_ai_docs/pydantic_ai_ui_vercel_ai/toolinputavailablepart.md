### ToolInputAvailablePart

Bases: `BaseUIPart`

Tool part in input-available state.

Source code in `pydantic_ai_slim/pydantic_ai/ui/vercel_ai/request_types.py`

```python
class ToolInputAvailablePart(BaseUIPart):
    """Tool part in input-available state."""

    type: Annotated[str, Field(pattern=r'^tool-')]
    tool_call_id: str
    state: Literal['input-available'] = 'input-available'
    input: Any | None = None
    provider_executed: bool | None = None
    call_provider_metadata: ProviderMetadata | None = None

```
