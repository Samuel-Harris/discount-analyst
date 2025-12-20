### ToolReturnPart

Bases: `BaseToolReturnPart`

A tool return message, this encodes the result of running a tool.

Source code in `pydantic_ai_slim/pydantic_ai/messages.py`

```python
@dataclass(repr=False)
class ToolReturnPart(BaseToolReturnPart):
    """A tool return message, this encodes the result of running a tool."""

    _: KW_ONLY

    part_kind: Literal['tool-return'] = 'tool-return'
    """Part type identifier, this is available on all parts as a discriminator."""

```

#### part_kind

```python
part_kind: Literal['tool-return'] = 'tool-return'

```

Part type identifier, this is available on all parts as a discriminator.
