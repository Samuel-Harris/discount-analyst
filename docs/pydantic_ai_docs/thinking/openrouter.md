## OpenRouter

To enable thinking, use the OpenRouterModelSettings.openrouter_reasoning [model setting](../agents/#model-run-settings).

openrouter_thinking_part.py

```python
from pydantic_ai import Agent
from pydantic_ai.models.openrouter import OpenRouterModel, OpenRouterModelSettings

model = OpenRouterModel('openai/gpt-5')
settings = OpenRouterModelSettings(openrouter_reasoning={'effort': 'high'})
agent = Agent(model, model_settings=settings)
...

```
