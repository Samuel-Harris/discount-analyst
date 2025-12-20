## Groq

Groq supports different formats to receive thinking parts:

- `"raw"`: The thinking part is included in the text content inside `<think>` tags, which are automatically converted to ThinkingPart objects.
- `"hidden"`: The thinking part is not included in the text content.
- `"parsed"`: The thinking part has its own structured part in the response which is converted into a ThinkingPart object.

To enable thinking, use the GroqModelSettings.groq_reasoning_format [model setting](../agents/#model-run-settings):

groq_thinking_part.py

```python
from pydantic_ai import Agent
from pydantic_ai.models.groq import GroqModel, GroqModelSettings

model = GroqModel('qwen-qwq-32b')
settings = GroqModelSettings(groq_reasoning_format='parsed')
agent = Agent(model, model_settings=settings)
...

```
