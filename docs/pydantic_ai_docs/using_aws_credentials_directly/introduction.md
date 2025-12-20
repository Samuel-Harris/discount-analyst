model = BedrockConverseModel(
    'anthropic.claude-3-sonnet-20240229-v1:0',
    provider=BedrockProvider(
        region_name='us-east-1',
        aws_access_key_id='your-access-key',
        aws_secret_access_key='your-secret-key',
    ),
)
agent = Agent(model)
...

```

You can also pass a pre-configured boto3 client:

```python
import boto3

from pydantic_ai import Agent
from pydantic_ai.models.bedrock import BedrockConverseModel
from pydantic_ai.providers.bedrock import BedrockProvider
