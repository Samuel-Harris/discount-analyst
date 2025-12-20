### PartStartEvent

An event indicating that a new part has started.

If multiple `PartStartEvent`s are received with the same index, the new one should fully replace the old one.

Source code in `pydantic_ai_slim/pydantic_ai/messages.py`

```python
@dataclass(repr=False, kw_only=True)
class PartStartEvent:
    """An event indicating that a new part has started.

    If multiple `PartStartEvent`s are received with the same index,
    the new one should fully replace the old one.
    """

    index: int
    """The index of the part within the overall response parts list."""

    part: ModelResponsePart
    """The newly started `ModelResponsePart`."""

    previous_part_kind: (
        Literal['text', 'thinking', 'tool-call', 'builtin-tool-call', 'builtin-tool-return', 'file'] | None
    ) = None
    """The kind of the previous part, if any.

    This is useful for UI event streams to know whether to group parts of the same kind together when emitting events.
    """

    event_kind: Literal['part_start'] = 'part_start'
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

The newly started `ModelResponsePart`.

#### previous_part_kind

```python
previous_part_kind: (
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

The kind of the previous part, if any.

This is useful for UI event streams to know whether to group parts of the same kind together when emitting events.

#### event_kind

```python
event_kind: Literal['part_start'] = 'part_start'

```

Event type identifier, used as a discriminator.
