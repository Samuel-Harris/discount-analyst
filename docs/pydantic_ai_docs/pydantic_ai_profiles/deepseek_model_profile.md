### deepseek_model_profile

```python
deepseek_model_profile(
    model_name: str,
) -> ModelProfile | None

```

Get the model profile for a DeepSeek model.

Source code in `pydantic_ai_slim/pydantic_ai/profiles/deepseek.py`

```python
def deepseek_model_profile(model_name: str) -> ModelProfile | None:
    """Get the model profile for a DeepSeek model."""
    return ModelProfile(ignore_streamed_leading_whitespace='r1' in model_name)

```
