### OpenAIChatModelSettings

Bases: `ModelSettings`

Settings used for an OpenAI model request.

Source code in `pydantic_ai_slim/pydantic_ai/models/openai.py`

```python
class OpenAIChatModelSettings(ModelSettings, total=False):
    """Settings used for an OpenAI model request."""

    # ALL FIELDS MUST BE `openai_` PREFIXED SO YOU CAN MERGE THEM WITH OTHER MODELS.

    openai_reasoning_effort: ReasoningEffort
    """Constrains effort on reasoning for [reasoning models](https://platform.openai.com/docs/guides/reasoning).

    Currently supported values are `low`, `medium`, and `high`. Reducing reasoning effort can
    result in faster responses and fewer tokens used on reasoning in a response.
    """

    openai_logprobs: bool
    """Include log probabilities in the response.

    For Chat models, these will be included in `ModelResponse.provider_details['logprobs']`.
    For Responses models, these will be included in the response output parts `TextPart.provider_details['logprobs']`.
    """

    openai_top_logprobs: int
    """Include log probabilities of the top n tokens in the response."""

    openai_user: str
    """A unique identifier representing the end-user, which can help OpenAI monitor and detect abuse.

    See [OpenAI's safety best practices](https://platform.openai.com/docs/guides/safety-best-practices#end-user-ids) for more details.
    """

    openai_service_tier: Literal['auto', 'default', 'flex', 'priority']
    """The service tier to use for the model request.

    Currently supported values are `auto`, `default`, `flex`, and `priority`.
    For more information, see [OpenAI's service tiers documentation](https://platform.openai.com/docs/api-reference/chat/object#chat/object-service_tier).
    """

    openai_prediction: ChatCompletionPredictionContentParam
    """Enables [predictive outputs](https://platform.openai.com/docs/guides/predicted-outputs).

    This feature is currently only supported for some OpenAI models.
    """

```

#### openai_reasoning_effort

```python
openai_reasoning_effort: ReasoningEffort

```

Constrains effort on reasoning for [reasoning models](https://platform.openai.com/docs/guides/reasoning).

Currently supported values are `low`, `medium`, and `high`. Reducing reasoning effort can result in faster responses and fewer tokens used on reasoning in a response.

#### openai_logprobs

```python
openai_logprobs: bool

```

Include log probabilities in the response.

For Chat models, these will be included in `ModelResponse.provider_details['logprobs']`. For Responses models, these will be included in the response output parts `TextPart.provider_details['logprobs']`.

#### openai_top_logprobs

```python
openai_top_logprobs: int

```

Include log probabilities of the top n tokens in the response.

#### openai_user

```python
openai_user: str

```

A unique identifier representing the end-user, which can help OpenAI monitor and detect abuse.

See [OpenAI's safety best practices](https://platform.openai.com/docs/guides/safety-best-practices#end-user-ids) for more details.

#### openai_service_tier

```python
openai_service_tier: Literal[
    "auto", "default", "flex", "priority"
]

```

The service tier to use for the model request.

Currently supported values are `auto`, `default`, `flex`, and `priority`. For more information, see [OpenAI's service tiers documentation](https://platform.openai.com/docs/api-reference/chat/object#chat/object-service_tier).

#### openai_prediction

```python
openai_prediction: ChatCompletionPredictionContentParam

```

Enables [predictive outputs](https://platform.openai.com/docs/guides/predicted-outputs).

This feature is currently only supported for some OpenAI models.
