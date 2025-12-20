### Excluding prompts and completions

For privacy and security reasons, you may want to monitor your agent's behavior and performance without exposing sensitive user data or proprietary prompts in your observability platform. Pydantic AI allows you to exclude the actual content from instrumentation events while preserving the structural information needed for debugging and monitoring.

When `include_content=False` is set, Pydantic AI will exclude sensitive content from OpenTelemetry events, including user prompts and model completions, tool call arguments and responses, and any other message content.

[Learn about Gateway](../gateway) excluding_sensitive_content.py

```python
from pydantic_ai import Agent
from pydantic_ai.models.instrumented import InstrumentationSettings

instrumentation_settings = InstrumentationSettings(include_content=False)

agent = Agent('gateway/openai:gpt-5', instrument=instrumentation_settings)
