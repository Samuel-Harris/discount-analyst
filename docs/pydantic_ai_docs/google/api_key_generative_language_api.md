### API Key (Generative Language API)

To use Gemini via the Generative Language API, go to [aistudio.google.com](https://aistudio.google.com/apikey) and create an API key.

Once you have the API key, set it as an environment variable:

```bash
export GOOGLE_API_KEY=your-api-key

```

You can then use `GoogleModel` by name (where GLA stands for Generative Language API):

```python
from pydantic_ai import Agent

agent = Agent('google-gla:gemini-2.5-pro')
...

```

Or you can explicitly create the provider:

```python
from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider

provider = GoogleProvider(api_key='your-api-key')
model = GoogleModel('gemini-2.5-pro', provider=provider)
agent = Agent(model)
...

```
