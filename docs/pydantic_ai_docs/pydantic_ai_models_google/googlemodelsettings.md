### GoogleModelSettings

Bases: `ModelSettings`

Settings used for a Gemini model request.

Source code in `pydantic_ai_slim/pydantic_ai/models/google.py`

```python
class GoogleModelSettings(ModelSettings, total=False):
    """Settings used for a Gemini model request."""

    # ALL FIELDS MUST BE `gemini_` PREFIXED SO YOU CAN MERGE THEM WITH OTHER MODELS.

    google_safety_settings: list[SafetySettingDict]
    """The safety settings to use for the model.

    See <https://ai.google.dev/gemini-api/docs/safety-settings> for more information.
    """

    google_thinking_config: ThinkingConfigDict
    """The thinking configuration to use for the model.

    See <https://ai.google.dev/gemini-api/docs/thinking> for more information.
    """

    google_labels: dict[str, str]
    """User-defined metadata to break down billed charges. Only supported by the Vertex AI API.

    See the [Gemini API docs](https://cloud.google.com/vertex-ai/generative-ai/docs/multimodal/add-labels-to-api-calls) for use cases and limitations.
    """

    google_video_resolution: MediaResolution
    """The video resolution to use for the model.

    See <https://ai.google.dev/api/generate-content#MediaResolution> for more information.
    """

    google_cached_content: str
    """The name of the cached content to use for the model.

    See <https://ai.google.dev/gemini-api/docs/caching> for more information.
    """

```

#### google_safety_settings

```python
google_safety_settings: list[SafetySettingDict]

```

The safety settings to use for the model.

See <https://ai.google.dev/gemini-api/docs/safety-settings> for more information.

#### google_thinking_config

```python
google_thinking_config: ThinkingConfigDict

```

The thinking configuration to use for the model.

See <https://ai.google.dev/gemini-api/docs/thinking> for more information.

#### google_labels

```python
google_labels: dict[str, str]

```

User-defined metadata to break down billed charges. Only supported by the Vertex AI API.

See the [Gemini API docs](https://cloud.google.com/vertex-ai/generative-ai/docs/multimodal/add-labels-to-api-calls) for use cases and limitations.

#### google_video_resolution

```python
google_video_resolution: MediaResolution

```

The video resolution to use for the model.

See <https://ai.google.dev/api/generate-content#MediaResolution> for more information.

#### google_cached_content

```python
google_cached_content: str

```

The name of the cached content to use for the model.

See <https://ai.google.dev/gemini-api/docs/caching> for more information.
