### OpenAI

openai_with_retries.py

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from smart_retry_example import create_retrying_client

client = create_retrying_client()
model = OpenAIChatModel('gpt-5', provider=OpenAIProvider(http_client=client))
agent = Agent(model)

```
