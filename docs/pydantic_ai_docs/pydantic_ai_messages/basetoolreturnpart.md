### BaseToolReturnPart

Base class for tool return parts.

Source code in `pydantic_ai_slim/pydantic_ai/messages.py`

```python
@dataclass(repr=False)
class BaseToolReturnPart:
    """Base class for tool return parts."""

    tool_name: str
    """The name of the "tool" was called."""

    content: Any
    """The return value."""

    tool_call_id: str = field(default_factory=_generate_tool_call_id)
    """The tool call identifier, this is used by some models including OpenAI.

    In case the tool call id is not provided by the model, Pydantic AI will generate a random one.
    """

    _: KW_ONLY

    metadata: Any = None
    """Additional data that can be accessed programmatically by the application but is not sent to the LLM."""

    timestamp: datetime = field(default_factory=_now_utc)
    """The timestamp, when the tool returned."""

    def model_response_str(self) -> str:
        """Return a string representation of the content for the model."""
        if isinstance(self.content, str):
            return self.content
        else:
            return tool_return_ta.dump_json(self.content).decode()

    def model_response_object(self) -> dict[str, Any]:
        """Return a dictionary representation of the content, wrapping non-dict types appropriately."""
        # gemini supports JSON dict return values, but no other JSON types, hence we wrap anything else in a dict
        json_content = tool_return_ta.dump_python(self.content, mode='json')
        if isinstance(json_content, dict):
            return json_content  # type: ignore[reportUnknownReturn]
        else:
            return {'return_value': json_content}

    def otel_event(self, settings: InstrumentationSettings) -> Event:
        return Event(
            'gen_ai.tool.message',
            body={
                **({'content': self.content} if settings.include_content else {}),
                'role': 'tool',
                'id': self.tool_call_id,
                'name': self.tool_name,
            },
        )

    def otel_message_parts(self, settings: InstrumentationSettings) -> list[_otel_messages.MessagePart]:
        from .models.instrumented import InstrumentedModel

        part = _otel_messages.ToolCallResponsePart(
            type='tool_call_response',
            id=self.tool_call_id,
            name=self.tool_name,
        )

        if settings.include_content and self.content is not None:
            part['result'] = InstrumentedModel.serialize_any(self.content)

        return [part]

    def has_content(self) -> bool:
        """Return `True` if the tool return has content."""
        return self.content is not None  # pragma: no cover

    __repr__ = _utils.dataclasses_no_defaults_repr

```

#### tool_name

```python
tool_name: str

```

The name of the "tool" was called.

#### content

```python
content: Any

```

The return value.

#### tool_call_id

```python
tool_call_id: str = field(
    default_factory=generate_tool_call_id
)

```

The tool call identifier, this is used by some models including OpenAI.

In case the tool call id is not provided by the model, Pydantic AI will generate a random one.

#### metadata

```python
metadata: Any = None

```

Additional data that can be accessed programmatically by the application but is not sent to the LLM.

#### timestamp

```python
timestamp: datetime = field(default_factory=now_utc)

```

The timestamp, when the tool returned.

#### model_response_str

```python
model_response_str() -> str

```

Return a string representation of the content for the model.

Source code in `pydantic_ai_slim/pydantic_ai/messages.py`

```python
def model_response_str(self) -> str:
    """Return a string representation of the content for the model."""
    if isinstance(self.content, str):
        return self.content
    else:
        return tool_return_ta.dump_json(self.content).decode()

```

#### model_response_object

```python
model_response_object() -> dict[str, Any]

```

Return a dictionary representation of the content, wrapping non-dict types appropriately.

Source code in `pydantic_ai_slim/pydantic_ai/messages.py`

```python
def model_response_object(self) -> dict[str, Any]:
    """Return a dictionary representation of the content, wrapping non-dict types appropriately."""
    # gemini supports JSON dict return values, but no other JSON types, hence we wrap anything else in a dict
    json_content = tool_return_ta.dump_python(self.content, mode='json')
    if isinstance(json_content, dict):
        return json_content  # type: ignore[reportUnknownReturn]
    else:
        return {'return_value': json_content}

```

#### has_content

```python
has_content() -> bool

```

Return `True` if the tool return has content.

Source code in `pydantic_ai_slim/pydantic_ai/messages.py`

```python
def has_content(self) -> bool:
    """Return `True` if the tool return has content."""
    return self.content is not None  # pragma: no cover

```
