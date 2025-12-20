### Cerebras

To use [Cerebras](https://cerebras.ai/), you need to create an API key in the [Cerebras Console](https://cloud.cerebras.ai/).

You can set the `CEREBRAS_API_KEY` environment variable and use CerebrasProvider by name:

```python
from pydantic_ai import Agent

agent = Agent('cerebras:llama3.3-70b')
result = agent.run_sync('What is the capital of France?')
print(result.output)
#> The capital of France is Paris.

```

Or initialise the model and provider directly:

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.cerebras import CerebrasProvider

model = OpenAIChatModel(
    'llama3.3-70b',
    provider=CerebrasProvider(api_key='your-cerebras-api-key'),
)
agent = Agent(model)

result = agent.run_sync('What is the capital of France?')
print(result.output)
#> The capital of France is Paris.

```
