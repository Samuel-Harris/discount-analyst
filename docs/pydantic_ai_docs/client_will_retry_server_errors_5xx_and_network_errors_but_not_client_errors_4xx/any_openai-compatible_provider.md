### Any OpenAI-Compatible Provider

openai_compatible_with_retries.py

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from smart_retry_example import create_retrying_client

client = create_retrying_client()
model = OpenAIChatModel(
    'your-model-name',  # Replace with actual model name
    provider=OpenAIProvider(
        base_url='https://api.example.com/v1',  # Replace with actual API URL
        api_key='your-api-key',  # Replace with actual API key
        http_client=client
    )
)
agent = Agent(model)

```
