### from_profile

```python
from_profile(profile: ModelProfile | None) -> Self

```

Build a ModelProfile subclass instance from a ModelProfile instance.

Source code in `pydantic_ai_slim/pydantic_ai/profiles/__init__.py`

```python
@classmethod
def from_profile(cls, profile: ModelProfile | None) -> Self:
    """Build a ModelProfile subclass instance from a ModelProfile instance."""
    if isinstance(profile, cls):
        return profile
    return cls().update(profile)

```
