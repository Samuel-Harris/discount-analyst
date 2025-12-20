### AudioUrl

Bases: `FileUrl`

A URL to an audio file.

Source code in `pydantic_ai_slim/pydantic_ai/messages.py`

```python
@dataclass(init=False, repr=False)
class AudioUrl(FileUrl):
    """A URL to an audio file."""

    url: str
    """The URL of the audio file."""

    _: KW_ONLY

    kind: Literal['audio-url'] = 'audio-url'
    """Type identifier, this is available on all parts as a discriminator."""

    def __init__(
        self,
        url: str,
        *,
        media_type: str | None = None,
        identifier: str | None = None,
        force_download: bool = False,
        vendor_metadata: dict[str, Any] | None = None,
        kind: Literal['audio-url'] = 'audio-url',
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

    def _infer_media_type(self) -> AudioMediaType:
        """Return the media type of the audio file, based on the url.

        References:
        - Gemini: https://ai.google.dev/gemini-api/docs/audio#supported-formats
        """
        if self.url.endswith('.mp3'):
            return 'audio/mpeg'
        if self.url.endswith('.wav'):
            return 'audio/wav'
        if self.url.endswith('.flac'):
            return 'audio/flac'
        if self.url.endswith('.oga'):
            return 'audio/ogg'
        if self.url.endswith('.aiff'):
            return 'audio/aiff'
        if self.url.endswith('.aac'):
            return 'audio/aac'

        raise ValueError(
            f'Could not infer media type from audio URL: {self.url}. Explicitly provide a `media_type` instead.'
        )

    @property
    def format(self) -> AudioFormat:
        """The file format of the audio file."""
        return _audio_format_lookup[self.media_type]

```

#### url

```python
url: str

```

The URL of the audio file.

#### kind

```python
kind: Literal['audio-url'] = kind

```

Type identifier, this is available on all parts as a discriminator.

#### format

```python
format: AudioFormat

```

The file format of the audio file.
