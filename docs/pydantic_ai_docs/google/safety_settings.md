### Safety settings

You can customize the safety settings by setting the `google_safety_settings` field.

```python
from google.genai.types import HarmBlockThreshold, HarmCategory

from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel, GoogleModelSettings

model_settings = GoogleModelSettings(
    google_safety_settings=[
        {
            'category': HarmCategory.HARM_CATEGORY_HATE_SPEECH,
            'threshold': HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
        }
    ]
)
model = GoogleModel('gemini-2.5-flash')
agent = Agent(model, model_settings=model_settings)
...

```

See the [Gemini API docs](https://ai.google.dev/gemini-api/docs/safety-settings) for more on safety settings.
