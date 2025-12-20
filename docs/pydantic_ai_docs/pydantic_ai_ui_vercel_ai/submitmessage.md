### SubmitMessage

Bases: `CamelBaseModel`

Submit message request.

Source code in `pydantic_ai_slim/pydantic_ai/ui/vercel_ai/request_types.py`

```python
class SubmitMessage(CamelBaseModel, extra='allow'):
    """Submit message request."""

    trigger: Literal['submit-message'] = 'submit-message'
    id: str
    messages: list[UIMessage]

```
