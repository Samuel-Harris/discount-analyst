### BuiltinToolReturnPart

Bases: `BaseToolReturnPart`

A tool return message from a built-in tool.

Source code in `pydantic_ai_slim/pydantic_ai/messages.py`

```python
@dataclass(repr=False)
class BuiltinToolReturnPart(BaseToolReturnPart):
    """A tool return message from a built-in tool."""

    _: KW_ONLY

    provider_name: str | None = None
    """The name of the provider that generated the response."""

    provider_details: dict[str, Any] | None = None
    """Additional data returned by the provider that can't be mapped to standard fields.

    This is used for data that is required to be sent back to APIs, as well as data users may want to access programmatically."""

    part_kind: Literal['builtin-tool-return'] = 'builtin-tool-return'
    """Part type identifier, this is available on all parts as a discriminator."""

```

#### provider_name

```python
provider_name: str | None = None

```

The name of the provider that generated the response.

#### provider_details

```python
provider_details: dict[str, Any] | None = None

```

Additional data returned by the provider that can't be mapped to standard fields.

This is used for data that is required to be sent back to APIs, as well as data users may want to access programmatically.

#### part_kind

```python
part_kind: Literal["builtin-tool-return"] = (
    "builtin-tool-return"
)

```

Part type identifier, this is available on all parts as a discriminator.
