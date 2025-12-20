### openai_model_profile

```python
openai_model_profile(model_name: str) -> ModelProfile

```

Get the model profile for an OpenAI model.

Source code in `pydantic_ai_slim/pydantic_ai/profiles/openai.py`

```python
def openai_model_profile(model_name: str) -> ModelProfile:
    """Get the model profile for an OpenAI model."""
    is_gpt_5 = model_name.startswith('gpt-5')
    is_o_series = model_name.startswith('o')
    is_reasoning_model = is_o_series or (is_gpt_5 and 'gpt-5-chat' not in model_name)

    # Check if the model supports web search (only specific search-preview models)
    supports_web_search = '-search-preview' in model_name

    # Structured Outputs (output mode 'native') is only supported with the gpt-4o-mini, gpt-4o-mini-2024-07-18, and gpt-4o-2024-08-06 model snapshots and later.
    # We leave it in here for all models because the `default_structured_output_mode` is `'tool'`, so `native` is only used
    # when the user specifically uses the `NativeOutput` marker, so an error from the API is acceptable.

    if is_reasoning_model:
        openai_unsupported_model_settings = (
            'temperature',
            'top_p',
            'presence_penalty',
            'frequency_penalty',
            'logit_bias',
            'logprobs',
            'top_logprobs',
        )
    else:
        openai_unsupported_model_settings = ()

    # The o1-mini model doesn't support the `system` role, so we default to `user`.
    # See https://github.com/pydantic/pydantic-ai/issues/974 for more details.
    openai_system_prompt_role = 'user' if model_name.startswith('o1-mini') else None

    return OpenAIModelProfile(
        json_schema_transformer=OpenAIJsonSchemaTransformer,
        supports_json_schema_output=True,
        supports_json_object_output=True,
        supports_image_output=is_gpt_5 or 'o3' in model_name or '4.1' in model_name or '4o' in model_name,
        openai_unsupported_model_settings=openai_unsupported_model_settings,
        openai_system_prompt_role=openai_system_prompt_role,
        openai_chat_supports_web_search=supports_web_search,
        openai_supports_encrypted_reasoning_content=is_reasoning_model,
    )

```
