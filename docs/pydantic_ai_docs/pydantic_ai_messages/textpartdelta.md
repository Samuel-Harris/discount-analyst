### TextPartDelta

A partial update (delta) for a `TextPart` to append new text content.

Source code in `pydantic_ai_slim/pydantic_ai/messages.py`

```python
@dataclass(repr=False)
class TextPartDelta:
    """A partial update (delta) for a `TextPart` to append new text content."""

    content_delta: str
    """The incremental text content to add to the existing `TextPart` content."""

    _: KW_ONLY

    provider_details: dict[str, Any] | None = None
    """Additional data returned by the provider that can't be mapped to standard fields.

    This is used for data that is required to be sent back to APIs, as well as data users may want to access programmatically."""

    part_delta_kind: Literal['text'] = 'text'
    """Part delta type identifier, used as a discriminator."""

    def apply(self, part: ModelResponsePart) -> TextPart:
        """Apply this text delta to an existing `TextPart`.

        Args:
            part: The existing model response part, which must be a `TextPart`.

        Returns:
            A new `TextPart` with updated text content.

        Raises:
            ValueError: If `part` is not a `TextPart`.
        """
        if not isinstance(part, TextPart):
            raise ValueError('Cannot apply TextPartDeltas to non-TextParts')  # pragma: no cover
        return replace(
            part,
            content=part.content + self.content_delta,
            provider_details={**(part.provider_details or {}), **(self.provider_details or {})} or None,
        )

    __repr__ = _utils.dataclasses_no_defaults_repr

```

#### content_delta

```python
content_delta: str

```

The incremental text content to add to the existing `TextPart` content.

#### provider_details

```python
provider_details: dict[str, Any] | None = None

```

Additional data returned by the provider that can't be mapped to standard fields.

This is used for data that is required to be sent back to APIs, as well as data users may want to access programmatically.

#### part_delta_kind

```python
part_delta_kind: Literal['text'] = 'text'

```

Part delta type identifier, used as a discriminator.

#### apply

```python
apply(part: ModelResponsePart) -> TextPart

```

Apply this text delta to an existing `TextPart`.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `part` | `ModelResponsePart` | The existing model response part, which must be a TextPart. | _required_ |

Returns:

| Type | Description | | --- | --- | | `TextPart` | A new TextPart with updated text content. |

Raises:

| Type | Description | | --- | --- | | `ValueError` | If part is not a TextPart. |

Source code in `pydantic_ai_slim/pydantic_ai/messages.py`

```python
def apply(self, part: ModelResponsePart) -> TextPart:
    """Apply this text delta to an existing `TextPart`.

    Args:
        part: The existing model response part, which must be a `TextPart`.

    Returns:
        A new `TextPart` with updated text content.

    Raises:
        ValueError: If `part` is not a `TextPart`.
    """
    if not isinstance(part, TextPart):
        raise ValueError('Cannot apply TextPartDeltas to non-TextParts')  # pragma: no cover
    return replace(
        part,
        content=part.content + self.content_delta,
        provider_details={**(part.provider_details or {}), **(self.provider_details or {})} or None,
    )

```
