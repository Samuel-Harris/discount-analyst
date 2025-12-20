### ReasoningUIPart

Bases: `BaseUIPart`

A reasoning part of a message.

Source code in `pydantic_ai_slim/pydantic_ai/ui/vercel_ai/request_types.py`

```python
class ReasoningUIPart(BaseUIPart):
    """A reasoning part of a message."""

    type: Literal['reasoning'] = 'reasoning'

    text: str
    """The reasoning text."""

    state: Literal['streaming', 'done'] | None = None
    """The state of the reasoning part."""

    provider_metadata: ProviderMetadata | None = None
    """The provider metadata."""

```

#### text

```python
text: str

```

The reasoning text.

#### state

```python
state: Literal['streaming', 'done'] | None = None

```

The state of the reasoning part.

#### provider_metadata

```python
provider_metadata: ProviderMetadata | None = None

```

The provider metadata.
