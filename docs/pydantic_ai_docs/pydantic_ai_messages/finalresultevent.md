### FinalResultEvent

An event indicating the response to the current model request matches the output schema and will produce a result.

Source code in `pydantic_ai_slim/pydantic_ai/messages.py`

```python
@dataclass(repr=False, kw_only=True)
class FinalResultEvent:
    """An event indicating the response to the current model request matches the output schema and will produce a result."""

    tool_name: str | None
    """The name of the output tool that was called. `None` if the result is from text content and not from a tool."""
    tool_call_id: str | None
    """The tool call ID, if any, that this result is associated with."""
    event_kind: Literal['final_result'] = 'final_result'
    """Event type identifier, used as a discriminator."""

    __repr__ = _utils.dataclasses_no_defaults_repr

```

#### tool_name

```python
tool_name: str | None

```

The name of the output tool that was called. `None` if the result is from text content and not from a tool.

#### tool_call_id

```python
tool_call_id: str | None

```

The tool call ID, if any, that this result is associated with.

#### event_kind

```python
event_kind: Literal['final_result'] = 'final_result'

```

Event type identifier, used as a discriminator.
