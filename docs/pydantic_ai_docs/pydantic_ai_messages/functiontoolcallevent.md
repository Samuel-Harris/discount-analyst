### FunctionToolCallEvent

An event indicating the start to a call to a function tool.

Source code in `pydantic_ai_slim/pydantic_ai/messages.py`

```python
@dataclass(repr=False)
class FunctionToolCallEvent:
    """An event indicating the start to a call to a function tool."""

    part: ToolCallPart
    """The (function) tool call to make."""

    _: KW_ONLY

    event_kind: Literal['function_tool_call'] = 'function_tool_call'
    """Event type identifier, used as a discriminator."""

    @property
    def tool_call_id(self) -> str:
        """An ID used for matching details about the call to its result."""
        return self.part.tool_call_id

    @property
    @deprecated('`call_id` is deprecated, use `tool_call_id` instead.')
    def call_id(self) -> str:
        """An ID used for matching details about the call to its result."""
        return self.part.tool_call_id  # pragma: no cover

    __repr__ = _utils.dataclasses_no_defaults_repr

```

#### part

```python
part: ToolCallPart

```

The (function) tool call to make.

#### event_kind

```python
event_kind: Literal["function_tool_call"] = (
    "function_tool_call"
)

```

Event type identifier, used as a discriminator.

#### tool_call_id

```python
tool_call_id: str

```

An ID used for matching details about the call to its result.

#### call_id

```python
call_id: str

```

An ID used for matching details about the call to its result.
