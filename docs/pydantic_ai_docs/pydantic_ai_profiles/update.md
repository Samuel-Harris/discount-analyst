### update

```python
update(profile: ModelProfile | None) -> Self

```

Update this ModelProfile (subclass) instance with the non-default values from another ModelProfile instance.

Source code in `pydantic_ai_slim/pydantic_ai/profiles/__init__.py`

```python
def update(self, profile: ModelProfile | None) -> Self:
    """Update this ModelProfile (subclass) instance with the non-default values from another ModelProfile instance."""
    if not profile:
        return self
    field_names = set(f.name for f in fields(self))
    non_default_attrs = {
        f.name: getattr(profile, f.name)
        for f in fields(profile)
        if f.name in field_names and getattr(profile, f.name) != f.default
    }
    return replace(self, **non_default_attrs)

```
