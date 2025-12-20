export AWS_ACCESS_KEY_ID='your-access-key'
export AWS_SECRET_ACCESS_KEY='your-secret-key'
export AWS_DEFAULT_REGION='us-east-1'  # or your preferred region

```

You can then use `BedrockConverseModel` by name:

[Learn about Gateway](../../gateway)

```python
from pydantic_ai import Agent

agent = Agent('gateway/bedrock:anthropic.claude-3-sonnet-20240229-v1:0')
...

```

```python
from pydantic_ai import Agent

agent = Agent('bedrock:anthropic.claude-3-sonnet-20240229-v1:0')
...

```

Or initialize the model directly with just the model name:

```python
from pydantic_ai import Agent
from pydantic_ai.models.bedrock import BedrockConverseModel

model = BedrockConverseModel('anthropic.claude-3-sonnet-20240229-v1:0')
agent = Agent(model)
...

```
