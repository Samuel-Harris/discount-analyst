### MoonshotAI

Create an API key in the [Moonshot Console](https://platform.moonshot.ai/console).

You can set the `MOONSHOTAI_API_KEY` environment variable and use MoonshotAIProvider by name:

```python
from pydantic_ai import Agent

agent = Agent('moonshotai:kimi-k2-0711-preview')
...

```

Or initialise the model and provider directly:

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.moonshotai import MoonshotAIProvider

model = OpenAIChatModel(
    'kimi-k2-0711-preview',
    provider=MoonshotAIProvider(api_key='your-moonshot-api-key'),
)
agent = Agent(model)
...

```
