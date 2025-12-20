## Custom HTTP Client

You can customize the `GoogleProvider` with a custom `httpx.AsyncClient`:

```python
from httpx import AsyncClient

from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider

custom_http_client = AsyncClient(timeout=30)
model = GoogleModel(
    'gemini-2.5-pro',
    provider=GoogleProvider(api_key='your-api-key', http_client=custom_http_client),
)
agent = Agent(model)
...

```
