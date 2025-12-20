### Anthropic

anthropic_with_retries.py

```python
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.providers.anthropic import AnthropicProvider

from smart_retry_example import create_retrying_client

client = create_retrying_client()
model = AnthropicModel('claude-sonnet-4-5-20250929', provider=AnthropicProvider(http_client=client))
agent = Agent(model)

```
