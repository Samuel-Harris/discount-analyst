### BuiltinToolCallEvent

Deprecated

`BuiltinToolCallEvent` is deprecated, look for `PartStartEvent` and `PartDeltaEvent` with `BuiltinToolCallPart` instead.

An event indicating the start to a call to a built-in tool.

Source code in `pydantic_ai_slim/pydantic_ai/messages.py`

```python
@deprecated(
    '`BuiltinToolCallEvent` is deprecated, look for `PartStartEvent` and `PartDeltaEvent` with `BuiltinToolCallPart` instead.'
)
@dataclass(repr=False)
class BuiltinToolCallEvent:
    """An event indicating the start to a call to a built-in tool."""

    part: BuiltinToolCallPart
    """The built-in tool call to make."""

    _: KW_ONLY

    event_kind: Literal['builtin_tool_call'] = 'builtin_tool_call'
    """Event type identifier, used as a discriminator."""

```

#### part

```python
part: BuiltinToolCallPart

```

The built-in tool call to make.

#### event_kind

```python
event_kind: Literal["builtin_tool_call"] = (
    "builtin_tool_call"
)

```

Event type identifier, used as a discriminator.
