### bedrock_amazon_model_profile

```python
bedrock_amazon_model_profile(
    model_name: str,
) -> ModelProfile | None

```

Get the model profile for an Amazon model used via Bedrock.

Source code in `pydantic_ai_slim/pydantic_ai/providers/bedrock.py`

```python
def bedrock_amazon_model_profile(model_name: str) -> ModelProfile | None:
    """Get the model profile for an Amazon model used via Bedrock."""
    profile = amazon_model_profile(model_name)
    if 'nova' in model_name:
        return BedrockModelProfile(bedrock_supports_tool_choice=True).update(profile)
    return profile

```
