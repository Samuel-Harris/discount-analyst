### BinaryImage

Bases: `BinaryContent`

Binary content that's guaranteed to be an image.

Source code in `pydantic_ai_slim/pydantic_ai/messages.py`

```python
class BinaryImage(BinaryContent):
    """Binary content that's guaranteed to be an image."""

    def __init__(
        self,
        data: bytes,
        *,
        media_type: str,
        identifier: str | None = None,
        vendor_metadata: dict[str, Any] | None = None,
        # Required for inline-snapshot which expects all dataclass `__init__` methods to take all field names as kwargs.
        kind: Literal['binary'] = 'binary',
        _identifier: str | None = None,
    ):
        super().__init__(
            data=data, media_type=media_type, identifier=identifier or _identifier, vendor_metadata=vendor_metadata
        )

        if not self.is_image:
            raise ValueError('`BinaryImage` must be have a media type that starts with "image/"')  # pragma: no cover

```
