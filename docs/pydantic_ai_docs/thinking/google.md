## Google

To enable thinking, use the GoogleModelSettings.google_thinking_config [model setting](../agents/#model-run-settings).

google_thinking_part.py

```python
from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel, GoogleModelSettings

model = GoogleModel('gemini-2.5-pro')
settings = GoogleModelSettings(google_thinking_config={'include_thoughts': True})
agent = Agent(model, model_settings=settings)
...

```
