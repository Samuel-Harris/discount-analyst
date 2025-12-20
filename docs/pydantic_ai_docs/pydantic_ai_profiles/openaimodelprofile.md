### OpenAIModelProfile

Bases: `ModelProfile`

Profile for models used with `OpenAIChatModel`.

ALL FIELDS MUST BE `openai_` PREFIXED SO YOU CAN MERGE THEM WITH OTHER MODELS.

Source code in `pydantic_ai_slim/pydantic_ai/profiles/openai.py`

```python
@dataclass(kw_only=True)
class OpenAIModelProfile(ModelProfile):
    """Profile for models used with `OpenAIChatModel`.

    ALL FIELDS MUST BE `openai_` PREFIXED SO YOU CAN MERGE THEM WITH OTHER MODELS.
    """

    openai_chat_thinking_field: str | None = None
    """Non-standard field name used by some providers for model thinking content in Chat Completions API responses.

    Plenty of providers use custom field names for thinking content. Ollama and newer versions of vLLM use `reasoning`,
    while DeepSeek, older vLLM and some others use `reasoning_content`.

    Notice that the thinking field configured here is currently limited to `str` type content.

    If `openai_chat_send_back_thinking_parts` is set to `'field'`, this field must be set to a non-None value."""

    openai_chat_send_back_thinking_parts: Literal['tags', 'field', False] = 'tags'
    """Whether the model includes thinking content in requests.

    This can be:
    * `'tags'` (default): The thinking content is included in the main `content` field, enclosed within thinking tags as
    specified in `thinking_tags` profile option.
    * `'field'`: The thinking content is included in a separate field specified by `openai_chat_thinking_field`.
    * `False`: No thinking content is sent in the request.

    Defaults to `'thinking_tags'` for backward compatibility reasons."""

    openai_supports_strict_tool_definition: bool = True
    """This can be set by a provider or user if the OpenAI-"compatible" API doesn't support strict tool definitions."""

    openai_supports_sampling_settings: bool = True
    """Turn off to don't send sampling settings like `temperature` and `top_p` to models that don't support them, like OpenAI's o-series reasoning models."""

    openai_unsupported_model_settings: Sequence[str] = ()
    """A list of model settings that are not supported by this model."""

    # Some OpenAI-compatible providers (e.g. MoonshotAI) currently do **not** accept
    # `tool_choice="required"`.  This flag lets the calling model know whether it's
    # safe to pass that value along.  Default is `True` to preserve existing
    # behaviour for OpenAI itself and most providers.
    openai_supports_tool_choice_required: bool = True
    """Whether the provider accepts the value ``tool_choice='required'`` in the request payload."""

    openai_system_prompt_role: OpenAISystemPromptRole | None = None
    """The role to use for the system prompt message. If not provided, defaults to `'system'`."""

    openai_chat_supports_web_search: bool = False
    """Whether the model supports web search in Chat Completions API."""

    openai_supports_encrypted_reasoning_content: bool = False
    """Whether the model supports including encrypted reasoning content in the response."""

    openai_responses_requires_function_call_status_none: bool = False
    """Whether the Responses API requires the `status` field on function tool calls to be `None`.

    This is required by vLLM Responses API versions before https://github.com/vllm-project/vllm/pull/26706.
    See https://github.com/pydantic/pydantic-ai/issues/3245 for more details.
    """

    def __post_init__(self):  # pragma: no cover
        if not self.openai_supports_sampling_settings:
            warnings.warn(
                'The `openai_supports_sampling_settings` has no effect, and it will be removed in future versions. '
                'Use `openai_unsupported_model_settings` instead.',
                DeprecationWarning,
            )
        if self.openai_chat_send_back_thinking_parts == 'field' and not self.openai_chat_thinking_field:
            raise UserError(
                'If `openai_chat_send_back_thinking_parts` is "field", '
                '`openai_chat_thinking_field` must be set to a non-None value.'
            )

```

#### openai_chat_thinking_field

```python
openai_chat_thinking_field: str | None = None

```

Non-standard field name used by some providers for model thinking content in Chat Completions API responses.

Plenty of providers use custom field names for thinking content. Ollama and newer versions of vLLM use `reasoning`, while DeepSeek, older vLLM and some others use `reasoning_content`.

Notice that the thinking field configured here is currently limited to `str` type content.

If `openai_chat_send_back_thinking_parts` is set to `'field'`, this field must be set to a non-None value.

#### openai_chat_send_back_thinking_parts

```python
openai_chat_send_back_thinking_parts: Literal[
    "tags", "field", False
] = "tags"

```

Whether the model includes thinking content in requests.

This can be: _ `'tags'` (default): The thinking content is included in the main `content` field, enclosed within thinking tags as specified in `thinking_tags` profile option. _ `'field'`: The thinking content is included in a separate field specified by `openai_chat_thinking_field`. \* `False`: No thinking content is sent in the request.

Defaults to `'thinking_tags'` for backward compatibility reasons.

#### openai_supports_strict_tool_definition

```python
openai_supports_strict_tool_definition: bool = True

```

This can be set by a provider or user if the OpenAI-"compatible" API doesn't support strict tool definitions.

#### openai_supports_sampling_settings

```python
openai_supports_sampling_settings: bool = True

```

Turn off to don't send sampling settings like `temperature` and `top_p` to models that don't support them, like OpenAI's o-series reasoning models.

#### openai_unsupported_model_settings

```python
openai_unsupported_model_settings: Sequence[str] = ()

```

A list of model settings that are not supported by this model.

#### openai_supports_tool_choice_required

```python
openai_supports_tool_choice_required: bool = True

```

Whether the provider accepts the value `tool_choice='required'` in the request payload.

#### openai_system_prompt_role

```python
openai_system_prompt_role: OpenAISystemPromptRole | None = (
    None
)

```

The role to use for the system prompt message. If not provided, defaults to `'system'`.

#### openai_chat_supports_web_search

```python
openai_chat_supports_web_search: bool = False

```

Whether the model supports web search in Chat Completions API.

#### openai_supports_encrypted_reasoning_content

```python
openai_supports_encrypted_reasoning_content: bool = False

```

Whether the model supports including encrypted reasoning content in the response.

#### openai_responses_requires_function_call_status_none

```python
openai_responses_requires_function_call_status_none: (
    bool
) = False

```

Whether the Responses API requires the `status` field on function tool calls to be `None`.

This is required by vLLM Responses API versions before https://github.com/vllm-project/vllm/pull/26706. See https://github.com/pydantic/pydantic-ai/issues/3245 for more details.
