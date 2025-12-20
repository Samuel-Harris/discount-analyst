## OpenAI Responses API

Pydantic AI also supports OpenAI's [Responses API](https://platform.openai.com/docs/api-reference/responses) through the

You can use OpenAIResponsesModel by name:

[Learn about Gateway](../../gateway)

```python
from pydantic_ai import Agent

agent = Agent('gateway/openai-responses:gpt-5')
...

```

```python
from pydantic_ai import Agent

agent = Agent('openai-responses:gpt-5')
...

```

Or initialise the model directly with just the model name:

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIResponsesModel

model = OpenAIResponsesModel('gpt-5')
agent = Agent(model)
...

```

You can learn more about the differences between the Responses API and Chat Completions API in the [OpenAI API docs](https://platform.openai.com/docs/guides/migrate-to-responses).
