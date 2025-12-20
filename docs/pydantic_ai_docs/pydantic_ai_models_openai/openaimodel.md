### OpenAIModel

Bases: `OpenAIChatModel`

Deprecated

`OpenAIModel` was renamed to `OpenAIChatModel` to clearly distinguish it from `OpenAIResponsesModel` which uses OpenAI's newer Responses API. Use that unless you're using an OpenAI Chat Completions-compatible API, or require a feature that the Responses API doesn't support yet like audio.

Deprecated alias for `OpenAIChatModel`.

Source code in `pydantic_ai_slim/pydantic_ai/models/openai.py`

```python
@deprecated(
    '`OpenAIModel` was renamed to `OpenAIChatModel` to clearly distinguish it from `OpenAIResponsesModel` which '
    "uses OpenAI's newer Responses API. Use that unless you're using an OpenAI Chat Completions-compatible API, or "
    "require a feature that the Responses API doesn't support yet like audio."
)
@dataclass(init=False)
class OpenAIModel(OpenAIChatModel):
    """Deprecated alias for `OpenAIChatModel`."""

```
