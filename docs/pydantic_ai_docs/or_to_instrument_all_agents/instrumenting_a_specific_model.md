### Instrumenting a specific `Model`

instrumented_model_example.py

```python
from pydantic_ai import Agent
from pydantic_ai.models.instrumented import InstrumentationSettings, InstrumentedModel

settings = InstrumentationSettings()
model = InstrumentedModel('openai:gpt-5', settings)
agent = Agent(model)

```
