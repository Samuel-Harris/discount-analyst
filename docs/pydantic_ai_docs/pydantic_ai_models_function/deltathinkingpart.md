### DeltaThinkingPart

Incremental change to a thinking part.

Used to describe a chunk when streaming thinking responses.

Source code in `pydantic_ai_slim/pydantic_ai/models/function.py`

```python
@dataclass(kw_only=True)
class DeltaThinkingPart:
    """Incremental change to a thinking part.

    Used to describe a chunk when streaming thinking responses.
    """

    content: str | None = None
    """Incremental change to the thinking content."""
    signature: str | None = None
    """Incremental change to the thinking signature."""

```

#### content

```python
content: str | None = None

```

Incremental change to the thinking content.

#### signature

```python
signature: str | None = None

```

Incremental change to the thinking signature.
