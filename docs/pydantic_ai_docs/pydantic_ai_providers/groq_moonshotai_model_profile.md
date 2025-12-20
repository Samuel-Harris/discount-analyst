### groq_moonshotai_model_profile

```python
groq_moonshotai_model_profile(
    model_name: str,
) -> ModelProfile | None

```

Get the model profile for an MoonshotAI model used with the Groq provider.

Source code in `pydantic_ai_slim/pydantic_ai/providers/groq.py`

```python
def groq_moonshotai_model_profile(model_name: str) -> ModelProfile | None:
    """Get the model profile for an MoonshotAI model used with the Groq provider."""
    return ModelProfile(supports_json_object_output=True, supports_json_schema_output=True).update(
        moonshotai_model_profile(model_name)
    )

```
