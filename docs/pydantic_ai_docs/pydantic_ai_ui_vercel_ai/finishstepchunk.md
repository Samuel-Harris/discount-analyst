### FinishStepChunk

Bases: `BaseChunk`

Finish step chunk.

Source code in `pydantic_ai_slim/pydantic_ai/ui/vercel_ai/response_types.py`

```python
class FinishStepChunk(BaseChunk):
    """Finish step chunk."""

    type: Literal['finish-step'] = 'finish-step'

```
