### GroqModelSettings

Bases: `ModelSettings`

Settings used for a Groq model request.

Source code in `pydantic_ai_slim/pydantic_ai/models/groq.py`

```python
class GroqModelSettings(ModelSettings, total=False):
    """Settings used for a Groq model request."""

    # ALL FIELDS MUST BE `groq_` PREFIXED SO YOU CAN MERGE THEM WITH OTHER MODELS.

    groq_reasoning_format: Literal['hidden', 'raw', 'parsed']
    """The format of the reasoning output.

    See [the Groq docs](https://console.groq.com/docs/reasoning#reasoning-format) for more details.
    """

```

#### groq_reasoning_format

```python
groq_reasoning_format: Literal['hidden', 'raw', 'parsed']

```

The format of the reasoning output.

See [the Groq docs](https://console.groq.com/docs/reasoning#reasoning-format) for more details.
