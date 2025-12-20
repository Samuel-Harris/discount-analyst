### IncompleteToolCall

Bases: `UnexpectedModelBehavior`

Error raised when a model stops due to token limit while emitting a tool call.

Source code in `pydantic_ai_slim/pydantic_ai/exceptions.py`

```python
class IncompleteToolCall(UnexpectedModelBehavior):
    """Error raised when a model stops due to token limit while emitting a tool call."""

```
