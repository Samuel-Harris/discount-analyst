### Disable thinking

On models older than Gemini 2.5 Pro, you can disable thinking by setting the `thinking_budget` to `0` on the `google_thinking_config`:

```python
from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel, GoogleModelSettings

model_settings = GoogleModelSettings(google_thinking_config={'thinking_budget': 0})
model = GoogleModel('gemini-2.5-flash')
agent = Agent(model, model_settings=model_settings)
...

```

Check out the [Gemini API docs](https://ai.google.dev/gemini-api/docs/thinking) for more on thinking.
