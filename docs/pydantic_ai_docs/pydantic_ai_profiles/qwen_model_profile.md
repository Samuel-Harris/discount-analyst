### qwen_model_profile

```python
qwen_model_profile(model_name: str) -> ModelProfile | None

```

Get the model profile for a Qwen model.

Source code in `pydantic_ai_slim/pydantic_ai/profiles/qwen.py`

```python
def qwen_model_profile(model_name: str) -> ModelProfile | None:
    """Get the model profile for a Qwen model."""
    if model_name.startswith('qwen-3-coder'):
        return OpenAIModelProfile(
            json_schema_transformer=InlineDefsJsonSchemaTransformer,
            openai_supports_tool_choice_required=False,
            openai_supports_strict_tool_definition=False,
            ignore_streamed_leading_whitespace=True,
        )
    return ModelProfile(
        json_schema_transformer=InlineDefsJsonSchemaTransformer,
        ignore_streamed_leading_whitespace=True,
    )

```
