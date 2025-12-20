## Environment variable

Once you have the API key, you can set it as an environment variable:

```bash
export OPENAI_API_KEY='your-api-key'

```

You can then use `OpenAIChatModel` by name:

[Learn about Gateway](../../gateway)

```python
from pydantic_ai import Agent

agent = Agent('gateway/openai:gpt-5')
...

```

```python
from pydantic_ai import Agent

agent = Agent('openai:gpt-5')
...

```

Or initialise the model directly with just the model name:

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel

model = OpenAIChatModel('gpt-5')
agent = Agent(model)
...

```

By default, the `OpenAIChatModel` uses the `OpenAIProvider` with the `base_url` set to `https://api.openai.com/v1`.
