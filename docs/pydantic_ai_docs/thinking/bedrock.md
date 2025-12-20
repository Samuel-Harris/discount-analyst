## Bedrock

Although Bedrock Converse doesn't provide a unified API to enable thinking, you can still use BedrockModelSettings.bedrock_additional_model_requests_fields [model setting](../agents/#model-run-settings) to pass provider-specific configuration:

bedrock_claude_thinking_part.py

```python
from pydantic_ai import Agent
from pydantic_ai.models.bedrock import BedrockConverseModel, BedrockModelSettings

model = BedrockConverseModel('us.anthropic.claude-sonnet-4-5-20250929-v1:0')
model_settings = BedrockModelSettings(
    bedrock_additional_model_requests_fields={
        'thinking': {'type': 'enabled', 'budget_tokens': 1024}
    }
)
agent = Agent(model=model, model_settings=model_settings)

```

bedrock_openai_thinking_part.py

```python
from pydantic_ai import Agent
from pydantic_ai.models.bedrock import BedrockConverseModel, BedrockModelSettings

model = BedrockConverseModel('openai.gpt-oss-120b-1:0')
model_settings = BedrockModelSettings(
    bedrock_additional_model_requests_fields={'reasoning_effort': 'low'}
)
agent = Agent(model=model, model_settings=model_settings)

```

bedrock_qwen_thinking_part.py

```python
from pydantic_ai import Agent
from pydantic_ai.models.bedrock import BedrockConverseModel, BedrockModelSettings

model = BedrockConverseModel('qwen.qwen3-32b-v1:0')
model_settings = BedrockModelSettings(
    bedrock_additional_model_requests_fields={'reasoning_config': 'high'}
)
agent = Agent(model=model, model_settings=model_settings)

```

Reasoning is [always enabled](https://docs.aws.amazon.com/bedrock/latest/userguide/inference-reasoning.html) for Deepseek model

bedrock_deepseek_thinking_part.py

```python
from pydantic_ai import Agent
from pydantic_ai.models.bedrock import BedrockConverseModel

model = BedrockConverseModel('us.deepseek.r1-v1:0')
agent = Agent(model=model)

```
