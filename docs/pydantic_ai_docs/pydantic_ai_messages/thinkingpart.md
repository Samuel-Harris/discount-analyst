### ThinkingPart

A thinking response from a model.

Source code in `pydantic_ai_slim/pydantic_ai/messages.py`

```python
@dataclass(repr=False)
class ThinkingPart:
    """A thinking response from a model."""

    content: str
    """The thinking content of the response."""

    _: KW_ONLY

    id: str | None = None
    """The identifier of the thinking part."""

    signature: str | None = None
    """The signature of the thinking.

    Supported by:

    * Anthropic (corresponds to the `signature` field)
    * Bedrock (corresponds to the `signature` field)
    * Google (corresponds to the `thought_signature` field)
    * OpenAI (corresponds to the `encrypted_content` field)
    """

    provider_name: str | None = None
    """The name of the provider that generated the response.

    Signatures are only sent back to the same provider.
    """

    provider_details: dict[str, Any] | None = None
    """Additional data returned by the provider that can't be mapped to standard fields.

    This is used for data that is required to be sent back to APIs, as well as data users may want to access programmatically."""

    part_kind: Literal['thinking'] = 'thinking'
    """Part type identifier, this is available on all parts as a discriminator."""

    def has_content(self) -> bool:
        """Return `True` if the thinking content is non-empty."""
        return bool(self.content)

    __repr__ = _utils.dataclasses_no_defaults_repr

```

#### content

```python
content: str

```

The thinking content of the response.

#### id

```python
id: str | None = None

```

The identifier of the thinking part.

#### signature

```python
signature: str | None = None

```

The signature of the thinking.

Supported by:

- Anthropic (corresponds to the `signature` field)
- Bedrock (corresponds to the `signature` field)
- Google (corresponds to the `thought_signature` field)
- OpenAI (corresponds to the `encrypted_content` field)

#### provider_name

```python
provider_name: str | None = None

```

The name of the provider that generated the response.

Signatures are only sent back to the same provider.

#### provider_details

```python
provider_details: dict[str, Any] | None = None

```

Additional data returned by the provider that can't be mapped to standard fields.

This is used for data that is required to be sent back to APIs, as well as data users may want to access programmatically.

#### part_kind

```python
part_kind: Literal['thinking'] = 'thinking'

```

Part type identifier, this is available on all parts as a discriminator.

#### has_content

```python
has_content() -> bool

```

Return `True` if the thinking content is non-empty.

Source code in `pydantic_ai_slim/pydantic_ai/messages.py`

```python
def has_content(self) -> bool:
    """Return `True` if the thinking content is non-empty."""
    return bool(self.content)

```
