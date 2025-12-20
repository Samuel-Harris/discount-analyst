### ToolOutputErrorPart

Bases: `BaseUIPart`

Tool part in output-error state.

Source code in `pydantic_ai_slim/pydantic_ai/ui/vercel_ai/request_types.py`

```python
class ToolOutputErrorPart(BaseUIPart):
    """Tool part in output-error state."""

    type: Annotated[str, Field(pattern=r'^tool-')]
    tool_call_id: str
    state: Literal['output-error'] = 'output-error'
    input: Any | None = None
    raw_input: Any | None = None
    error_text: str
    provider_executed: bool | None = None
    call_provider_metadata: ProviderMetadata | None = None

```
