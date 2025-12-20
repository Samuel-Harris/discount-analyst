### UserPromptPart

A user prompt, generally written by the end user.

Content comes from the `user_prompt` parameter of Agent.run, Agent.run_sync, and Agent.run_stream.

Source code in `pydantic_ai_slim/pydantic_ai/messages.py`

```python
@dataclass(repr=False)
class UserPromptPart:
    """A user prompt, generally written by the end user.

    Content comes from the `user_prompt` parameter of [`Agent.run`][pydantic_ai.agent.AbstractAgent.run],
    [`Agent.run_sync`][pydantic_ai.agent.AbstractAgent.run_sync], and [`Agent.run_stream`][pydantic_ai.agent.AbstractAgent.run_stream].
    """

    content: str | Sequence[UserContent]
    """The content of the prompt."""

    _: KW_ONLY

    timestamp: datetime = field(default_factory=_now_utc)
    """The timestamp of the prompt."""

    part_kind: Literal['user-prompt'] = 'user-prompt'
    """Part type identifier, this is available on all parts as a discriminator."""

    def otel_event(self, settings: InstrumentationSettings) -> Event:
        content = [{'kind': part.pop('type'), **part} for part in self.otel_message_parts(settings)]
        for part in content:
            if part['kind'] == 'binary' and 'content' in part:
                part['binary_content'] = part.pop('content')
        content = [
            part['content'] if part == {'kind': 'text', 'content': part.get('content')} else part for part in content
        ]
        if content in ([{'kind': 'text'}], [self.content]):
            content = content[0]
        return Event('gen_ai.user.message', body={'content': content, 'role': 'user'})

    def otel_message_parts(self, settings: InstrumentationSettings) -> list[_otel_messages.MessagePart]:
        parts: list[_otel_messages.MessagePart] = []
        content: Sequence[UserContent] = [self.content] if isinstance(self.content, str) else self.content
        for part in content:
            if isinstance(part, str):
                parts.append(
                    _otel_messages.TextPart(type='text', **({'content': part} if settings.include_content else {}))
                )
            elif isinstance(part, ImageUrl | AudioUrl | DocumentUrl | VideoUrl):
                parts.append(
                    _otel_messages.MediaUrlPart(
                        type=part.kind,
                        **{'url': part.url} if settings.include_content else {},
                    )
                )
            elif isinstance(part, BinaryContent):
                converted_part = _otel_messages.BinaryDataPart(type='binary', media_type=part.media_type)
                if settings.include_content and settings.include_binary_content:
                    converted_part['content'] = base64.b64encode(part.data).decode()
                parts.append(converted_part)
            elif isinstance(part, CachePoint):
                # CachePoint is a marker, not actual content - skip it for otel
                pass
            else:
                parts.append({'type': part.kind})  # pragma: no cover
        return parts

    __repr__ = _utils.dataclasses_no_defaults_repr

```

#### content

```python
content: str | Sequence[UserContent]

```

The content of the prompt.

#### timestamp

```python
timestamp: datetime = field(default_factory=now_utc)

```

The timestamp of the prompt.

#### part_kind

```python
part_kind: Literal['user-prompt'] = 'user-prompt'

```

Part type identifier, this is available on all parts as a discriminator.
