### Together AI

Go to [Together.ai](https://www.together.ai/) and create an API key in your account settings.

You can set the `TOGETHER_API_KEY` environment variable and use TogetherProvider by name:

```python
from pydantic_ai import Agent

agent = Agent('together:meta-llama/Llama-3.3-70B-Instruct-Turbo-Free')
...

```

Or initialise the model and provider directly:

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.together import TogetherProvider

model = OpenAIChatModel(
    'meta-llama/Llama-3.3-70B-Instruct-Turbo-Free',  # model library available at https://www.together.ai/models
    provider=TogetherProvider(api_key='your-together-api-key'),
)
agent = Agent(model)
...

```
