### google_model_profile

```python
google_model_profile(
    model_name: str,
) -> ModelProfile | None

```

Get the model profile for a Google model.

Source code in `pydantic_ai_slim/pydantic_ai/profiles/google.py`

```python
def google_model_profile(model_name: str) -> ModelProfile | None:
    """Get the model profile for a Google model."""
    is_image_model = 'image' in model_name
    is_3_or_newer = 'gemini-3' in model_name
    return GoogleModelProfile(
        json_schema_transformer=GoogleJsonSchemaTransformer,
        supports_image_output=is_image_model,
        supports_json_schema_output=is_3_or_newer or not is_image_model,
        supports_json_object_output=is_3_or_newer or not is_image_model,
        supports_tools=not is_image_model,
        google_supports_native_output_with_builtin_tools=is_3_or_newer,
    )

```
