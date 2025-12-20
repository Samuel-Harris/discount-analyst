### meta_groq_model_profile

```python
meta_groq_model_profile(
    model_name: str,
) -> ModelProfile | None

```

Get the model profile for a Meta model used with the Groq provider.

Source code in `pydantic_ai_slim/pydantic_ai/providers/groq.py`

```python
def meta_groq_model_profile(model_name: str) -> ModelProfile | None:
    """Get the model profile for a Meta model used with the Groq provider."""
    if model_name in {'llama-4-maverick-17b-128e-instruct', 'llama-4-scout-17b-16e-instruct'}:
        return ModelProfile(supports_json_object_output=True, supports_json_schema_output=True).update(
            meta_model_profile(model_name)
        )
    else:
        return meta_model_profile(model_name)

```
