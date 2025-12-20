## Error Handling

The retry transports will re-raise the last exception if all retry attempts fail. Make sure to handle these appropriately in your application:

error_handling_example.py

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from smart_retry_example import create_retrying_client

client = create_retrying_client()
model = OpenAIChatModel('gpt-5', provider=OpenAIProvider(http_client=client))
agent = Agent(model)

```
