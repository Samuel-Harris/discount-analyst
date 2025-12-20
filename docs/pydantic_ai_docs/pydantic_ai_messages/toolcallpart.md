### ToolCallPart

Bases: `BaseToolCallPart`

A tool call from a model.

Source code in `pydantic_ai_slim/pydantic_ai/messages.py`

```python
@dataclass(repr=False)
class ToolCallPart(BaseToolCallPart):
    """A tool call from a model."""

    _: KW_ONLY

    part_kind: Literal['tool-call'] = 'tool-call'
    """Part type identifier, this is available on all parts as a discriminator."""

```

#### part_kind

```python
part_kind: Literal['tool-call'] = 'tool-call'

```

Part type identifier, this is available on all parts as a discriminator.
