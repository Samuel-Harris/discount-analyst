### Per-Model Settings

You can configure different ModelSettings for each model in a fallback chain by passing the `settings` parameter when creating each model. This is particularly useful when different providers have different optimal configurations:

fallback_model_per_settings.py

```python
from pydantic_ai import Agent, ModelSettings
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.fallback import FallbackModel
from pydantic_ai.models.openai import OpenAIChatModel
