## `provider` argument

You can provide a custom `BedrockProvider` via the `provider` argument. This is useful when you want to specify credentials directly or use a custom boto3 client:

```python
from pydantic_ai import Agent
from pydantic_ai.models.bedrock import BedrockConverseModel
from pydantic_ai.providers.bedrock import BedrockProvider
