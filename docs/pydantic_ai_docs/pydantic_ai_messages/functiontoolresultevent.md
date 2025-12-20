### FunctionToolResultEvent

An event indicating the result of a function tool call.

Source code in `pydantic_ai_slim/pydantic_ai/messages.py`

```python
@dataclass(repr=False)
class FunctionToolResultEvent:
    """An event indicating the result of a function tool call."""

    result: ToolReturnPart | RetryPromptPart
    """The result of the call to the function tool."""

    _: KW_ONLY

    content: str | Sequence[UserContent] | None = None
    """The content that will be sent to the model as a UserPromptPart following the result."""

    event_kind: Literal['function_tool_result'] = 'function_tool_result'
    """Event type identifier, used as a discriminator."""

    @property
    def tool_call_id(self) -> str:
        """An ID used to match the result to its original call."""
        return self.result.tool_call_id

    __repr__ = _utils.dataclasses_no_defaults_repr

```

#### result

```python
result: ToolReturnPart | RetryPromptPart

```

The result of the call to the function tool.

#### content

```python
content: str | Sequence[UserContent] | None = None

```

The content that will be sent to the model as a UserPromptPart following the result.

#### event_kind

```python
event_kind: Literal["function_tool_result"] = (
    "function_tool_result"
)

```

Event type identifier, used as a discriminator.

#### tool_call_id

```python
tool_call_id: str

```

An ID used to match the result to its original call.
