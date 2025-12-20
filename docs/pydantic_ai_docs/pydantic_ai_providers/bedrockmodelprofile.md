### BedrockModelProfile

Bases: `ModelProfile`

Profile for models used with BedrockModel.

ALL FIELDS MUST BE `bedrock_` PREFIXED SO YOU CAN MERGE THEM WITH OTHER MODELS.

Source code in `pydantic_ai_slim/pydantic_ai/providers/bedrock.py`

```python
@dataclass(kw_only=True)
class BedrockModelProfile(ModelProfile):
    """Profile for models used with BedrockModel.

    ALL FIELDS MUST BE `bedrock_` PREFIXED SO YOU CAN MERGE THEM WITH OTHER MODELS.
    """

    bedrock_supports_tool_choice: bool = False
    bedrock_tool_result_format: Literal['text', 'json'] = 'text'
    bedrock_send_back_thinking_parts: bool = False

```
