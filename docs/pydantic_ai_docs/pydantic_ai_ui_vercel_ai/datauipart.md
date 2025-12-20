### DataUIPart

Bases: `BaseUIPart`

Data part with dynamic type based on data name.

Source code in `pydantic_ai_slim/pydantic_ai/ui/vercel_ai/request_types.py`

```python
class DataUIPart(BaseUIPart):
    """Data part with dynamic type based on data name."""

    type: Annotated[str, Field(pattern=r'^data-')]
    id: str | None = None
    data: Any

```
