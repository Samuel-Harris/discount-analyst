### StepStartUIPart

Bases: `BaseUIPart`

A step boundary part of a message.

Source code in `pydantic_ai_slim/pydantic_ai/ui/vercel_ai/request_types.py`

```python
class StepStartUIPart(BaseUIPart):
    """A step boundary part of a message."""

    type: Literal['step-start'] = 'step-start'

```
