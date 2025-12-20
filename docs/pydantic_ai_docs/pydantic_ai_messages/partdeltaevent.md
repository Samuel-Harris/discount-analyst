### PartDeltaEvent

An event indicating a delta update for an existing part.

Source code in `pydantic_ai_slim/pydantic_ai/messages.py`

```python
@dataclass(repr=False, kw_only=True)
class PartDeltaEvent:
    """An event indicating a delta update for an existing part."""

    index: int
    """The index of the part within the overall response parts list."""

    delta: ModelResponsePartDelta
    """The delta to apply to the specified part."""

    event_kind: Literal['part_delta'] = 'part_delta'
    """Event type identifier, used as a discriminator."""

    __repr__ = _utils.dataclasses_no_defaults_repr

```

#### index

```python
index: int

```

The index of the part within the overall response parts list.

#### delta

```python
delta: ModelResponsePartDelta

```

The delta to apply to the specified part.

#### event_kind

```python
event_kind: Literal['part_delta'] = 'part_delta'

```

Event type identifier, used as a discriminator.
