## `provider` argument

You can provide a custom `Provider` via the `provider` argument:

```python
from pydantic_ai import Agent
from pydantic_ai.models.cohere import CohereModel
from pydantic_ai.providers.cohere import CohereProvider

model = CohereModel('command-r7b-12-2024', provider=CohereProvider(api_key='your-api-key'))
agent = Agent(model)
...

```

You can also customize the `CohereProvider` with a custom `http_client`:

```python
from httpx import AsyncClient

from pydantic_ai import Agent
from pydantic_ai.models.cohere import CohereModel
from pydantic_ai.providers.cohere import CohereProvider

custom_http_client = AsyncClient(timeout=30)
model = CohereModel(
    'command-r7b-12-2024',
    provider=CohereProvider(api_key='your-api-key', http_client=custom_http_client),
)
agent = Agent(model)
...

```
