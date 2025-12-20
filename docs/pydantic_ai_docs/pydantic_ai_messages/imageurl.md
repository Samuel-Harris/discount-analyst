### ImageUrl

Bases: `FileUrl`

A URL to an image.

Source code in `pydantic_ai_slim/pydantic_ai/messages.py`

```python
@dataclass(init=False, repr=False)
class ImageUrl(FileUrl):
    """A URL to an image."""

    url: str
    """The URL of the image."""

    _: KW_ONLY

    kind: Literal['image-url'] = 'image-url'
    """Type identifier, this is available on all parts as a discriminator."""

    def __init__(
        self,
        url: str,
        *,
        media_type: str | None = None,
        identifier: str | None = None,
        force_download: bool = False,
        vendor_metadata: dict[str, Any] | None = None,
        kind: Literal['image-url'] = 'image-url',
        # Required for inline-snapshot which expects all dataclass `__init__` methods to take all field names as kwargs.
        _media_type: str | None = None,
        _identifier: str | None = None,
    ) -> None:
        super().__init__(
            url=url,
            force_download=force_download,
            vendor_metadata=vendor_metadata,
            media_type=media_type or _media_type,
            identifier=identifier or _identifier,
        )
        self.kind = kind

    def _infer_media_type(self) -> ImageMediaType:
        """Return the media type of the image, based on the url."""
        if self.url.endswith(('.jpg', '.jpeg')):
            return 'image/jpeg'
        elif self.url.endswith('.png'):
            return 'image/png'
        elif self.url.endswith('.gif'):
            return 'image/gif'
        elif self.url.endswith('.webp'):
            return 'image/webp'
        else:
            raise ValueError(
                f'Could not infer media type from image URL: {self.url}. Explicitly provide a `media_type` instead.'
            )

    @property
    def format(self) -> ImageFormat:
        """The file format of the image.

        The choice of supported formats were based on the Bedrock Converse API. Other APIs don't require to use a format.
        """
        return _image_format_lookup[self.media_type]

```

#### url

```python
url: str

```

The URL of the image.

#### kind

```python
kind: Literal['image-url'] = kind

```

Type identifier, this is available on all parts as a discriminator.

#### format

```python
format: ImageFormat

```

The file format of the image.

The choice of supported formats were based on the Bedrock Converse API. Other APIs don't require to use a format.
