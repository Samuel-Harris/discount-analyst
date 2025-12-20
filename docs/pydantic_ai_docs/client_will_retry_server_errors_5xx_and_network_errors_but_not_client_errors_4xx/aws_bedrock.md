### AWS Bedrock

The AWS Bedrock provider uses boto3's built-in retry mechanisms instead of httpx. To configure retries for Bedrock, use boto3's `Config`:

```python
from botocore.config import Config

config = Config(retries={'max_attempts': 5, 'mode': 'adaptive'})

```

See [Bedrock: Configuring Retries](../models/bedrock/#configuring-retries) for complete examples.
