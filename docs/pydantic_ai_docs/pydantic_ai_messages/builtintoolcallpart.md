### BuiltinToolCallPart

Bases: `BaseToolCallPart`

A tool call to a built-in tool.

Source code in `pydantic_ai_slim/pydantic_ai/messages.py`

```python
@dataclass(repr=False)
class BuiltinToolCallPart(BaseToolCallPart):
    """A tool call to a built-in tool."""

    _: KW_ONLY

    provider_name: str | None = None
    """The name of the provider that generated the response.

    Built-in tool calls are only sent back to the same provider.
    """

    part_kind: Literal['builtin-tool-call'] = 'builtin-tool-call'
    """Part type identifier, this is available on all parts as a discriminator."""

```

#### provider_name

```python
provider_name: str | None = None

```

The name of the provider that generated the response.

Built-in tool calls are only sent back to the same provider.

#### part_kind

```python
part_kind: Literal["builtin-tool-call"] = (
    "builtin-tool-call"
)

```

Part type identifier, this is available on all parts as a discriminator.
