## Fallback Model

You can use FallbackModel to attempt multiple models in sequence until one successfully returns a result. Under the hood, Pydantic AI automatically switches from one model to the next if the current model returns a 4xx or 5xx status code.

Note

The provider SDKs on which Models are based (like OpenAI, Anthropic, etc.) often have built-in retry logic that can delay the `FallbackModel` from activating.

When using `FallbackModel`, it's recommended to disable provider SDK retries to ensure immediate fallback, for example by setting `max_retries=0` on a [custom OpenAI client](../openai/#custom-openai-client).

In the following example, the agent first makes a request to the OpenAI model (which fails due to an invalid API key), and then falls back to the Anthropic model.

fallback_model.py

```python
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.fallback import FallbackModel
from pydantic_ai.models.openai import OpenAIChatModel

openai_model = OpenAIChatModel('gpt-5')
anthropic_model = AnthropicModel('claude-sonnet-4-5')
fallback_model = FallbackModel(openai_model, anthropic_model)

agent = Agent(fallback_model)
response = agent.run_sync('What is the capital of France?')
print(response.data)
#> Paris

print(response.all_messages())
"""
[
    ModelRequest(
        parts=[
            UserPromptPart(
                content='What is the capital of France?',
                timestamp=datetime.datetime(...),
                part_kind='user-prompt',
            )
        ],
        kind='request',
    ),
    ModelResponse(
        parts=[TextPart(content='Paris', part_kind='text')],
        model_name='claude-sonnet-4-5',
        timestamp=datetime.datetime(...),
        kind='response',
        provider_response_id=None,
    ),
]
"""

```

The `ModelResponse` message above indicates in the `model_name` field that the output was returned by the Anthropic model, which is the second model specified in the `FallbackModel`.

Note

Each model's options should be configured individually. For example, `base_url`, `api_key`, and custom clients should be set on each model itself, not on the `FallbackModel`.
