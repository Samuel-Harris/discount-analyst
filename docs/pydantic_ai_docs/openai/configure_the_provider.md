## Configure the provider

If you want to pass parameters in code to the provider, you can programmatically instantiate the OpenAIProvider and pass it to the model:

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

model = OpenAIChatModel('gpt-5', provider=OpenAIProvider(api_key='your-api-key'))
agent = Agent(model)
...

```
