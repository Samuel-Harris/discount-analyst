### MessageMetadataChunk

Bases: `BaseChunk`

Message metadata chunk.

Source code in `pydantic_ai_slim/pydantic_ai/ui/vercel_ai/response_types.py`

```python
class MessageMetadataChunk(BaseChunk):
    """Message metadata chunk."""

    type: Literal['message-metadata'] = 'message-metadata'
    message_metadata: Any

```
