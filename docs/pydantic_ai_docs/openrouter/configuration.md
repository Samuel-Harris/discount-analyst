## Configuration

To use [OpenRouter](https://openrouter.ai), first create an API key at [openrouter.ai/keys](https://openrouter.ai/keys).

You can set the `OPENROUTER_API_KEY` environment variable and use OpenRouterProvider by name:

```python
from pydantic_ai import Agent

agent = Agent('openrouter:anthropic/claude-3.5-sonnet')
...

```

Or initialise the model and provider directly:

```python
from pydantic_ai import Agent
from pydantic_ai.models.openrouter import OpenRouterModel
from pydantic_ai.providers.openrouter import OpenRouterProvider

model = OpenRouterModel(
    'anthropic/claude-3.5-sonnet',
    provider=OpenRouterProvider(api_key='your-openrouter-api-key'),
)
agent = Agent(model)
...

```
