## Customizing Bedrock Runtime API

You can customize the Bedrock Runtime API calls by adding additional parameters, such as [guardrail configurations](https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails.html) and [performance settings](https://docs.aws.amazon.com/bedrock/latest/userguide/latency-optimized-inference.html). For a complete list of configurable parameters, refer to the documentation for BedrockModelSettings.

customize_bedrock_model_settings.py

```python
from pydantic_ai import Agent
from pydantic_ai.models.bedrock import BedrockConverseModel, BedrockModelSettings
