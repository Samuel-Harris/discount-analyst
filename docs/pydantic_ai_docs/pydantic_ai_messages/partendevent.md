### PartEndEvent

An event indicating that a part is complete.

Source code in `pydantic_ai_slim/pydantic_ai/messages.py`

```python
@dataclass(repr=False, kw_only=True)
class PartEndEvent:
    """An event indicating that a part is complete."""

    index: int
    """The index of the part within the overall response parts list."""

    part: ModelResponsePart
    """The complete `ModelResponsePart`."""

    next_part_kind: (
        Literal['text', 'thinking', 'tool-call', 'builtin-tool-call', 'builtin-tool-return', 'file'] | None
    ) = None
    """The kind of the next part, if any.

    This is useful for UI event streams to know whether to group parts of the same kind together when emitting events.
    """

    event_kind: Literal['part_end'] = 'part_end'
    """Event type identifier, used as a discriminator."""

    __repr__ = _utils.dataclasses_no_defaults_repr

```

#### index

```python
index: int

```

The index of the part within the overall response parts list.

#### part

```python
part: ModelResponsePart

```

The complete `ModelResponsePart`.

#### next_part_kind

```python
next_part_kind: (
    Literal[
        "text",
        "thinking",
        "tool-call",
        "builtin-tool-call",
        "builtin-tool-return",
        "file",
    ]
    | None
) = None

```

The kind of the next part, if any.

This is useful for UI event streams to know whether to group parts of the same kind together when emitting events.

#### event_kind

```python
event_kind: Literal['part_end'] = 'part_end'

```

Event type identifier, used as a discriminator.
