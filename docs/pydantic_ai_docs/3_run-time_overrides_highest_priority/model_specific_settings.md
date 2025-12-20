### Model specific settings

If you wish to further customize model behavior, you can use a subclass of ModelSettings, like GoogleModelSettings, associated with your model of choice.

For example:

```python
from pydantic_ai import Agent, UnexpectedModelBehavior
from pydantic_ai.models.google import GoogleModelSettings

agent = Agent('google-gla:gemini-2.5-flash')

try:
    result = agent.run_sync(
        'Write a list of 5 very rude things that I might say to the universe after stubbing my toe in the dark:',
        model_settings=GoogleModelSettings(
            temperature=0.0,  # general model settings can also be specified
            gemini_safety_settings=[
                {
                    'category': 'HARM_CATEGORY_HARASSMENT',
                    'threshold': 'BLOCK_LOW_AND_ABOVE',
                },
                {
                    'category': 'HARM_CATEGORY_HATE_SPEECH',
                    'threshold': 'BLOCK_LOW_AND_ABOVE',
                },
            ],
        ),
    )
except UnexpectedModelBehavior as e:
    print(e)  # (1)!
    """
    Content filter 'SAFETY' triggered, body:
    <safety settings details>
    """

```

1. This error is raised because the safety thresholds were exceeded.
