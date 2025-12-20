## Anthropic

To enable thinking, use the AnthropicModelSettings.anthropic_thinking [model setting](../agents/#model-run-settings).

anthropic_thinking_part.py

```python
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel, AnthropicModelSettings

model = AnthropicModel('claude-sonnet-4-0')
settings = AnthropicModelSettings(
    anthropic_thinking={'type': 'enabled', 'budget_tokens': 1024},
)
agent = Agent(model, model_settings=settings)
...

```
