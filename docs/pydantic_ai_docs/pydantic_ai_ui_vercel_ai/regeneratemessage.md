### RegenerateMessage

Bases: `CamelBaseModel`

Ask the agent to regenerate a message.

Source code in `pydantic_ai_slim/pydantic_ai/ui/vercel_ai/request_types.py`

```python
class RegenerateMessage(CamelBaseModel, extra='allow'):
    """Ask the agent to regenerate a message."""

    trigger: Literal['regenerate-message']
    id: str
    messages: list[UIMessage]
    message_id: str

```
