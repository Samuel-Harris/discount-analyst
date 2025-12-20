## Environment variable

Once you have the API key, you can set it as an environment variable:

```bash
export CO_API_KEY='your-api-key'

```

You can then use `CohereModel` by name:

```python
from pydantic_ai import Agent

agent = Agent('cohere:command-r7b-12-2024')
...

```

Or initialise the model directly with just the model name:

```python
from pydantic_ai import Agent
from pydantic_ai.models.cohere import CohereModel

model = CohereModel('command-r7b-12-2024')
agent = Agent(model)
...

```
