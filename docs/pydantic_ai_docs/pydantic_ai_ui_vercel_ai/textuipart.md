### TextUIPart

Bases: `BaseUIPart`

A text part of a message.

Source code in `pydantic_ai_slim/pydantic_ai/ui/vercel_ai/request_types.py`

```python
class TextUIPart(BaseUIPart):
    """A text part of a message."""

    type: Literal['text'] = 'text'

    text: str
    """The text content."""

    state: Literal['streaming', 'done'] | None = None
    """The state of the text part."""

    provider_metadata: ProviderMetadata | None = None
    """The provider metadata."""

```

#### text

```python
text: str

```

The text content.

#### state

```python
state: Literal['streaming', 'done'] | None = None

```

The state of the text part.

#### provider_metadata

```python
provider_metadata: ProviderMetadata | None = None

```

The provider metadata.
