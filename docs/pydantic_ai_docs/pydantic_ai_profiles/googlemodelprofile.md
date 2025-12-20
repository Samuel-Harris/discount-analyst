### GoogleModelProfile

Bases: `ModelProfile`

Profile for models used with `GoogleModel`.

ALL FIELDS MUST BE `google_` PREFIXED SO YOU CAN MERGE THEM WITH OTHER MODELS.

Source code in `pydantic_ai_slim/pydantic_ai/profiles/google.py`

```python
@dataclass(kw_only=True)
class GoogleModelProfile(ModelProfile):
    """Profile for models used with `GoogleModel`.

    ALL FIELDS MUST BE `google_` PREFIXED SO YOU CAN MERGE THEM WITH OTHER MODELS.
    """

    google_supports_native_output_with_builtin_tools: bool = False
    """Whether the model supports native output with builtin tools.
    See https://ai.google.dev/gemini-api/docs/structured-output?example=recipe#structured_outputs_with_tools"""

```

#### google_supports_native_output_with_builtin_tools

```python
google_supports_native_output_with_builtin_tools: bool = (
    False
)

```

Whether the model supports native output with builtin tools. See https://ai.google.dev/gemini-api/docs/structured-output?example=recipe#structured_outputs_with_tools
