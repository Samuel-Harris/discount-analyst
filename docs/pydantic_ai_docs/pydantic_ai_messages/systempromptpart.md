### SystemPromptPart

A system prompt, generally written by the application developer.

This gives the model context and guidance on how to respond.

Source code in `pydantic_ai_slim/pydantic_ai/messages.py`

```python
@dataclass(repr=False)
class SystemPromptPart:
    """A system prompt, generally written by the application developer.

    This gives the model context and guidance on how to respond.
    """

    content: str
    """The content of the prompt."""

    _: KW_ONLY

    timestamp: datetime = field(default_factory=_now_utc)
    """The timestamp of the prompt."""

    dynamic_ref: str | None = None
    """The ref of the dynamic system prompt function that generated this part.

    Only set if system prompt is dynamic, see [`system_prompt`][pydantic_ai.Agent.system_prompt] for more information.
    """

    part_kind: Literal['system-prompt'] = 'system-prompt'
    """Part type identifier, this is available on all parts as a discriminator."""

    def otel_event(self, settings: InstrumentationSettings) -> Event:
        return Event(
            'gen_ai.system.message',
            body={'role': 'system', **({'content': self.content} if settings.include_content else {})},
        )

    def otel_message_parts(self, settings: InstrumentationSettings) -> list[_otel_messages.MessagePart]:
        return [_otel_messages.TextPart(type='text', **{'content': self.content} if settings.include_content else {})]

    __repr__ = _utils.dataclasses_no_defaults_repr

```

#### content

```python
content: str

```

The content of the prompt.

#### timestamp

```python
timestamp: datetime = field(default_factory=now_utc)

```

The timestamp of the prompt.

#### dynamic_ref

```python
dynamic_ref: str | None = None

```

The ref of the dynamic system prompt function that generated this part.

Only set if system prompt is dynamic, see system_prompt for more information.

#### part_kind

```python
part_kind: Literal['system-prompt'] = 'system-prompt'

```

Part type identifier, this is available on all parts as a discriminator.
