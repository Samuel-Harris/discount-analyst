### RetryPromptPart

A message back to a model asking it to try again.

This can be sent for a number of reasons:

- Pydantic validation of tool arguments failed, here content is derived from a Pydantic ValidationError
- a tool raised a ModelRetry exception
- no tool was found for the tool name
- the model returned plain text when a structured response was expected
- Pydantic validation of a structured response failed, here content is derived from a Pydantic ValidationError
- an output validator raised a ModelRetry exception

Source code in `pydantic_ai_slim/pydantic_ai/messages.py`

````python
@dataclass(repr=False)
class RetryPromptPart:
    """A message back to a model asking it to try again.

    This can be sent for a number of reasons:

    * Pydantic validation of tool arguments failed, here content is derived from a Pydantic
      [`ValidationError`][pydantic_core.ValidationError]
    * a tool raised a [`ModelRetry`][pydantic_ai.exceptions.ModelRetry] exception
    * no tool was found for the tool name
    * the model returned plain text when a structured response was expected
    * Pydantic validation of a structured response failed, here content is derived from a Pydantic
      [`ValidationError`][pydantic_core.ValidationError]
    * an output validator raised a [`ModelRetry`][pydantic_ai.exceptions.ModelRetry] exception
    """

    content: list[pydantic_core.ErrorDetails] | str
    """Details of why and how the model should retry.

    If the retry was triggered by a [`ValidationError`][pydantic_core.ValidationError], this will be a list of
    error details.
    """

    _: KW_ONLY

    tool_name: str | None = None
    """The name of the tool that was called, if any."""

    tool_call_id: str = field(default_factory=_generate_tool_call_id)
    """The tool call identifier, this is used by some models including OpenAI.

    In case the tool call id is not provided by the model, Pydantic AI will generate a random one.
    """

    timestamp: datetime = field(default_factory=_now_utc)
    """The timestamp, when the retry was triggered."""

    part_kind: Literal['retry-prompt'] = 'retry-prompt'
    """Part type identifier, this is available on all parts as a discriminator."""

    def model_response(self) -> str:
        """Return a string message describing why the retry is requested."""
        if isinstance(self.content, str):
            if self.tool_name is None:
                description = f'Validation feedback:\n{self.content}'
            else:
                description = self.content
        else:
            json_errors = error_details_ta.dump_json(self.content, exclude={'__all__': {'ctx'}}, indent=2)
            plural = isinstance(self.content, list) and len(self.content) != 1
            description = (
                f'{len(self.content)} validation error{"s" if plural else ""}:\n```json\n{json_errors.decode()}\n```'
            )
        return f'{description}\n\nFix the errors and try again.'

    def otel_event(self, settings: InstrumentationSettings) -> Event:
        if self.tool_name is None:
            return Event('gen_ai.user.message', body={'content': self.model_response(), 'role': 'user'})
        else:
            return Event(
                'gen_ai.tool.message',
                body={
                    **({'content': self.model_response()} if settings.include_content else {}),
                    'role': 'tool',
                    'id': self.tool_call_id,
                    'name': self.tool_name,
                },
            )

    def otel_message_parts(self, settings: InstrumentationSettings) -> list[_otel_messages.MessagePart]:
        if self.tool_name is None:
            return [_otel_messages.TextPart(type='text', content=self.model_response())]
        else:
            part = _otel_messages.ToolCallResponsePart(
                type='tool_call_response',
                id=self.tool_call_id,
                name=self.tool_name,
            )

            if settings.include_content:
                part['result'] = self.model_response()

            return [part]

    __repr__ = _utils.dataclasses_no_defaults_repr

````

#### content

```python
content: list[ErrorDetails] | str

```

Details of why and how the model should retry.

If the retry was triggered by a ValidationError, this will be a list of error details.

#### tool_name

```python
tool_name: str | None = None

```

The name of the tool that was called, if any.

#### tool_call_id

```python
tool_call_id: str = field(
    default_factory=generate_tool_call_id
)

```

The tool call identifier, this is used by some models including OpenAI.

In case the tool call id is not provided by the model, Pydantic AI will generate a random one.

#### timestamp

```python
timestamp: datetime = field(default_factory=now_utc)

```

The timestamp, when the retry was triggered.

#### part_kind

```python
part_kind: Literal['retry-prompt'] = 'retry-prompt'

```

Part type identifier, this is available on all parts as a discriminator.

#### model_response

```python
model_response() -> str

```

Return a string message describing why the retry is requested.

Source code in `pydantic_ai_slim/pydantic_ai/messages.py`

````python
def model_response(self) -> str:
    """Return a string message describing why the retry is requested."""
    if isinstance(self.content, str):
        if self.tool_name is None:
            description = f'Validation feedback:\n{self.content}'
        else:
            description = self.content
    else:
        json_errors = error_details_ta.dump_json(self.content, exclude={'__all__': {'ctx'}}, indent=2)
        plural = isinstance(self.content, list) and len(self.content) != 1
        description = (
            f'{len(self.content)} validation error{"s" if plural else ""}:\n```json\n{json_errors.decode()}\n```'
        )
    return f'{description}\n\nFix the errors and try again.'

````
