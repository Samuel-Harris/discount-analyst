### amazon_model_profile

```python
amazon_model_profile(
    model_name: str,
) -> ModelProfile | None

```

Get the model profile for an Amazon model.

Source code in `pydantic_ai_slim/pydantic_ai/profiles/amazon.py`

```python
def amazon_model_profile(model_name: str) -> ModelProfile | None:
    """Get the model profile for an Amazon model."""
    return ModelProfile(json_schema_transformer=InlineDefsJsonSchemaTransformer)

```
