### Fireworks AI

Go to [Fireworks.AI](https://fireworks.ai/) and create an API key in your account settings.

You can set the `FIREWORKS_API_KEY` environment variable and use FireworksProvider by name:

```python
from pydantic_ai import Agent

agent = Agent('fireworks:accounts/fireworks/models/qwq-32b')
...

```

Or initialise the model and provider directly:

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.fireworks import FireworksProvider

model = OpenAIChatModel(
    'accounts/fireworks/models/qwq-32b',  # model library available at https://fireworks.ai/models
    provider=FireworksProvider(api_key='your-fireworks-api-key'),
)
agent = Agent(model)
...

```
