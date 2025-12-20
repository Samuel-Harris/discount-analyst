### bedrock_deepseek_model_profile

```python
bedrock_deepseek_model_profile(
    model_name: str,
) -> ModelProfile | None

```

Get the model profile for a DeepSeek model used via Bedrock.

Source code in `pydantic_ai_slim/pydantic_ai/providers/bedrock.py`

```python
def bedrock_deepseek_model_profile(model_name: str) -> ModelProfile | None:
    """Get the model profile for a DeepSeek model used via Bedrock."""
    profile = deepseek_model_profile(model_name)
    if 'r1' in model_name:
        return BedrockModelProfile(bedrock_send_back_thinking_parts=True).update(profile)
    return profile  # pragma: no cover

```
