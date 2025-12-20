### TextPart

A plain text response from a model.

Source code in `pydantic_ai_slim/pydantic_ai/messages.py`

```python
@dataclass(repr=False)
class TextPart:
    """A plain text response from a model."""

    content: str
    """The text content of the response."""

    _: KW_ONLY

    id: str | None = None
    """An optional identifier of the text part."""

    provider_details: dict[str, Any] | None = None
    """Additional data returned by the provider that can't be mapped to standard fields.

    This is used for data that is required to be sent back to APIs, as well as data users may want to access programmatically."""

    part_kind: Literal['text'] = 'text'
    """Part type identifier, this is available on all parts as a discriminator."""

    def has_content(self) -> bool:
        """Return `True` if the text content is non-empty."""
        return bool(self.content)

    __repr__ = _utils.dataclasses_no_defaults_repr

```

#### content

```python
content: str

```

The text content of the response.

#### id

```python
id: str | None = None

```

An optional identifier of the text part.

#### provider_details

```python
provider_details: dict[str, Any] | None = None

```

Additional data returned by the provider that can't be mapped to standard fields.

This is used for data that is required to be sent back to APIs, as well as data users may want to access programmatically.

#### part_kind

```python
part_kind: Literal['text'] = 'text'

```

Part type identifier, this is available on all parts as a discriminator.

#### has_content

```python
has_content() -> bool

```

Return `True` if the text content is non-empty.

Source code in `pydantic_ai_slim/pydantic_ai/messages.py`

```python
def has_content(self) -> bool:
    """Return `True` if the text content is non-empty."""
    return bool(self.content)

```
