config = Config(
    retries={
        'max_attempts': 5,
        'mode': 'adaptive'  # Recommended for rate limiting
    }
)

bedrock_client = boto3.client(
    'bedrock-runtime',
    region_name='us-east-1',
    config=config
)

model = BedrockConverseModel(
    'us.amazon.nova-micro-v1:0',
    provider=BedrockProvider(bedrock_client=bedrock_client),
)
agent = Agent(model)

```
