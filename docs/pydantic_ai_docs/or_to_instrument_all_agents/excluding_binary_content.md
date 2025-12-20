### Excluding binary content

[Learn about Gateway](../gateway) excluding_binary_content.py

```python
from pydantic_ai import Agent, InstrumentationSettings

instrumentation_settings = InstrumentationSettings(include_binary_content=False)

agent = Agent('gateway/openai:gpt-5', instrument=instrumentation_settings)
