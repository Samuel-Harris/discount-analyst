## Configuring Retries

Bedrock uses boto3's built-in retry mechanisms. You can configure retry behavior by passing a custom boto3 client with retry settings:

```python
import boto3
from botocore.config import Config

from pydantic_ai import Agent
from pydantic_ai.models.bedrock import BedrockConverseModel
from pydantic_ai.providers.bedrock import BedrockProvider
