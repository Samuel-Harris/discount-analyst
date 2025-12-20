## Environment variable

Once you have the API key, you can set it as an environment variable:

```bash
export ANTHROPIC_API_KEY='your-api-key'

```

You can then use `AnthropicModel` by name:

[Learn about Gateway](../../gateway)

```python
from pydantic_ai import Agent

agent = Agent('gateway/anthropic:claude-sonnet-4-5')
...

```

```python
from pydantic_ai import Agent

agent = Agent('anthropic:claude-sonnet-4-5')
...

```

Or initialise the model directly with just the model name:

```python
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel

model = AnthropicModel('claude-sonnet-4-5')
agent = Agent(model)
...

```
