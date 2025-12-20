### ToolOutputAvailablePart

Bases: `BaseUIPart`

Tool part in output-available state.

Source code in `pydantic_ai_slim/pydantic_ai/ui/vercel_ai/request_types.py`

```python
class ToolOutputAvailablePart(BaseUIPart):
    """Tool part in output-available state."""

    type: Annotated[str, Field(pattern=r'^tool-')]
    tool_call_id: str
    state: Literal['output-available'] = 'output-available'
    input: Any | None = None
    output: Any | None = None
    provider_executed: bool | None = None
    call_provider_metadata: ProviderMetadata | None = None
    preliminary: bool | None = None

```
