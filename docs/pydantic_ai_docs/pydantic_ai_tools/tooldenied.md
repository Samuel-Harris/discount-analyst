### ToolDenied

Indicates that a tool call has been denied and that a denial message should be returned to the model.

Source code in `pydantic_ai_slim/pydantic_ai/tools.py`

```python
@dataclass
class ToolDenied:
    """Indicates that a tool call has been denied and that a denial message should be returned to the model."""

    message: str = 'The tool call was denied.'
    """The message to return to the model."""

    _: KW_ONLY

    kind: Literal['tool-denied'] = 'tool-denied'

```

#### message

```python
message: str = 'The tool call was denied.'

```

The message to return to the model.
