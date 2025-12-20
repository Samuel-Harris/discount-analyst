### meta_model_profile

```python
meta_model_profile(model_name: str) -> ModelProfile | None

```

Get the model profile for a Meta model.

Source code in `pydantic_ai_slim/pydantic_ai/profiles/meta.py`

```python
def meta_model_profile(model_name: str) -> ModelProfile | None:
    """Get the model profile for a Meta model."""
    return ModelProfile(json_schema_transformer=InlineDefsJsonSchemaTransformer)

```
