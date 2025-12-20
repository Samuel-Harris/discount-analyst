### VideoUrl

Bases: `FileUrl`

A URL to a video.

Source code in `pydantic_ai_slim/pydantic_ai/messages.py`

```python
@dataclass(init=False, repr=False)
class VideoUrl(FileUrl):
    """A URL to a video."""

    url: str
    """The URL of the video."""

    _: KW_ONLY

    kind: Literal['video-url'] = 'video-url'
    """Type identifier, this is available on all parts as a discriminator."""

    def __init__(
        self,
        url: str,
        *,
        media_type: str | None = None,
        identifier: str | None = None,
        force_download: bool = False,
        vendor_metadata: dict[str, Any] | None = None,
        kind: Literal['video-url'] = 'video-url',
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

    def _infer_media_type(self) -> VideoMediaType:
        """Return the media type of the video, based on the url."""
        if self.url.endswith('.mkv'):
            return 'video/x-matroska'
        elif self.url.endswith('.mov'):
            return 'video/quicktime'
        elif self.url.endswith('.mp4'):
            return 'video/mp4'
        elif self.url.endswith('.webm'):
            return 'video/webm'
        elif self.url.endswith('.flv'):
            return 'video/x-flv'
        elif self.url.endswith(('.mpeg', '.mpg')):
            return 'video/mpeg'
        elif self.url.endswith('.wmv'):
            return 'video/x-ms-wmv'
        elif self.url.endswith('.three_gp'):
            return 'video/3gpp'
        # Assume that YouTube videos are mp4 because there would be no extension
        # to infer from. This should not be a problem, as Gemini disregards media
        # type for YouTube URLs.
        elif self.is_youtube:
            return 'video/mp4'
        else:
            raise ValueError(
                f'Could not infer media type from video URL: {self.url}. Explicitly provide a `media_type` instead.'
            )

    @property
    def is_youtube(self) -> bool:
        """True if the URL has a YouTube domain."""
        return self.url.startswith(('https://youtu.be/', 'https://youtube.com/', 'https://www.youtube.com/'))

    @property
    def format(self) -> VideoFormat:
        """The file format of the video.

        The choice of supported formats were based on the Bedrock Converse API. Other APIs don't require to use a format.
        """
        return _video_format_lookup[self.media_type]

```

#### url

```python
url: str

```

The URL of the video.

#### kind

```python
kind: Literal['video-url'] = kind

```

Type identifier, this is available on all parts as a discriminator.

#### is_youtube

```python
is_youtube: bool

```

True if the URL has a YouTube domain.

#### format

```python
format: VideoFormat

```

The file format of the video.

The choice of supported formats were based on the Bedrock Converse API. Other APIs don't require to use a format.
