### BaseChunk

Bases: `CamelBaseModel`, `ABC`

Abstract base class for response SSE events.

Source code in `pydantic_ai_slim/pydantic_ai/ui/vercel_ai/response_types.py`

```python
class BaseChunk(CamelBaseModel, ABC):
    """Abstract base class for response SSE events."""

    def encode(self) -> str:
        return self.model_dump_json(by_alias=True, exclude_none=True)

```
