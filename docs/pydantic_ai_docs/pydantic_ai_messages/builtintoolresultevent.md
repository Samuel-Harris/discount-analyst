### BuiltinToolResultEvent

Deprecated

`BuiltinToolResultEvent` is deprecated, look for `PartStartEvent` and `PartDeltaEvent` with `BuiltinToolReturnPart` instead.

An event indicating the result of a built-in tool call.

Source code in `pydantic_ai_slim/pydantic_ai/messages.py`

```python
@deprecated(
    '`BuiltinToolResultEvent` is deprecated, look for `PartStartEvent` and `PartDeltaEvent` with `BuiltinToolReturnPart` instead.'
)
@dataclass(repr=False)
class BuiltinToolResultEvent:
    """An event indicating the result of a built-in tool call."""

    result: BuiltinToolReturnPart
    """The result of the call to the built-in tool."""

    _: KW_ONLY

    event_kind: Literal['builtin_tool_result'] = 'builtin_tool_result'
    """Event type identifier, used as a discriminator."""

```

#### result

```python
result: BuiltinToolReturnPart

```

The result of the call to the built-in tool.

#### event_kind

```python
event_kind: Literal["builtin_tool_result"] = (
    "builtin_tool_result"
)

```

Event type identifier, used as a discriminator.
