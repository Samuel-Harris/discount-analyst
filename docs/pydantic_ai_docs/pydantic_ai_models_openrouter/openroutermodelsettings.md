### OpenRouterModelSettings

Bases: `ModelSettings`

Settings used for an OpenRouter model request.

Source code in `pydantic_ai_slim/pydantic_ai/models/openrouter.py`

```python
class OpenRouterModelSettings(ModelSettings, total=False):
    """Settings used for an OpenRouter model request."""

    # ALL FIELDS MUST BE `openrouter_` PREFIXED SO YOU CAN MERGE THEM WITH OTHER MODELS.

    openrouter_models: list[str]
    """A list of fallback models.

    These models will be tried, in order, if the main model returns an error. [See details](https://openrouter.ai/docs/features/model-routing#the-models-parameter)
    """

    openrouter_provider: OpenRouterProviderConfig
    """OpenRouter routes requests to the best available providers for your model. By default, requests are load balanced across the top providers to maximize uptime.

    You can customize how your requests are routed using the provider object. [See more](https://openrouter.ai/docs/features/provider-routing)"""

    openrouter_preset: str
    """Presets allow you to separate your LLM configuration from your code.

    Create and manage presets through the OpenRouter web application to control provider routing, model selection, system prompts, and other parameters, then reference them in OpenRouter API requests. [See more](https://openrouter.ai/docs/features/presets)"""

    openrouter_transforms: list[OpenRouterTransforms]
    """To help with prompts that exceed the maximum context size of a model.

    Transforms work by removing or truncating messages from the middle of the prompt, until the prompt fits within the model's context window. [See more](https://openrouter.ai/docs/features/message-transforms)
    """

    openrouter_reasoning: OpenRouterReasoning
    """To control the reasoning tokens in the request.

    The reasoning config object consolidates settings for controlling reasoning strength across different models. [See more](https://openrouter.ai/docs/use-cases/reasoning-tokens)
    """

    openrouter_usage: OpenRouterUsageConfig
    """To control the usage of the model.

    The usage config object consolidates settings for enabling detailed usage information. [See more](https://openrouter.ai/docs/use-cases/usage-accounting)
    """

```

#### openrouter_models

```python
openrouter_models: list[str]

```

A list of fallback models.

These models will be tried, in order, if the main model returns an error. [See details](https://openrouter.ai/docs/features/model-routing#the-models-parameter)

#### openrouter_provider

```python
openrouter_provider: OpenRouterProviderConfig

```

OpenRouter routes requests to the best available providers for your model. By default, requests are load balanced across the top providers to maximize uptime.

You can customize how your requests are routed using the provider object. [See more](https://openrouter.ai/docs/features/provider-routing)

#### openrouter_preset

```python
openrouter_preset: str

```

Presets allow you to separate your LLM configuration from your code.

Create and manage presets through the OpenRouter web application to control provider routing, model selection, system prompts, and other parameters, then reference them in OpenRouter API requests. [See more](https://openrouter.ai/docs/features/presets)

#### openrouter_transforms

```python
openrouter_transforms: list[OpenRouterTransforms]

```

To help with prompts that exceed the maximum context size of a model.

Transforms work by removing or truncating messages from the middle of the prompt, until the prompt fits within the model's context window. [See more](https://openrouter.ai/docs/features/message-transforms)

#### openrouter_reasoning

```python
openrouter_reasoning: OpenRouterReasoning

```

To control the reasoning tokens in the request.

The reasoning config object consolidates settings for controlling reasoning strength across different models. [See more](https://openrouter.ai/docs/use-cases/reasoning-tokens)

#### openrouter_usage

```python
openrouter_usage: OpenRouterUsageConfig

```

To control the usage of the model.

The usage config object consolidates settings for enabling detailed usage information. [See more](https://openrouter.ai/docs/use-cases/usage-accounting)
