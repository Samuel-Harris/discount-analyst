### FileUrl

Bases: `ABC`

Abstract base class for any URL-based file.

Source code in `pydantic_ai_slim/pydantic_ai/messages.py`

```python
@dataclass(init=False, repr=False)
class FileUrl(ABC):
    """Abstract base class for any URL-based file."""

    url: str
    """The URL of the file."""

    _: KW_ONLY

    force_download: bool = False
    """For OpenAI and Google APIs it:

    * If True, the file is downloaded and the data is sent to the model as bytes.
    * If False, the URL is sent directly to the model and no download is performed.
    """

    vendor_metadata: dict[str, Any] | None = None
    """Vendor-specific metadata for the file.

    Supported by:
    - `GoogleModel`: `VideoUrl.vendor_metadata` is used as `video_metadata`: https://ai.google.dev/gemini-api/docs/video-understanding#customize-video-processing
    - `OpenAIChatModel`, `OpenAIResponsesModel`: `ImageUrl.vendor_metadata['detail']` is used as `detail` setting for images
    """

    _media_type: Annotated[str | None, pydantic.Field(alias='media_type', default=None, exclude=True)] = field(
        compare=False, default=None
    )

    _identifier: Annotated[str | None, pydantic.Field(alias='identifier', default=None, exclude=True)] = field(
        compare=False, default=None
    )

    def __init__(
        self,
        url: str,
        *,
        media_type: str | None = None,
        identifier: str | None = None,
        force_download: bool = False,
        vendor_metadata: dict[str, Any] | None = None,
    ) -> None:
        self.url = url
        self._media_type = media_type
        self._identifier = identifier
        self.force_download = force_download
        self.vendor_metadata = vendor_metadata

    @pydantic.computed_field
    @property
    def media_type(self) -> str:
        """Return the media type of the file, based on the URL or the provided `media_type`."""
        return self._media_type or self._infer_media_type()

    @pydantic.computed_field
    @property
    def identifier(self) -> str:
        """The identifier of the file, such as a unique ID.

        This identifier can be provided to the model in a message to allow it to refer to this file in a tool call argument,
        and the tool can look up the file in question by iterating over the message history and finding the matching `FileUrl`.

        This identifier is only automatically passed to the model when the `FileUrl` is returned by a tool.
        If you're passing the `FileUrl` as a user message, it's up to you to include a separate text part with the identifier,
        e.g. "This is file <identifier>:" preceding the `FileUrl`.

        It's also included in inline-text delimiters for providers that require inlining text documents, so the model can
        distinguish multiple files.
        """
        return self._identifier or _multi_modal_content_identifier(self.url)

    @abstractmethod
    def _infer_media_type(self) -> str:
        """Infer the media type of the file based on the URL."""
        raise NotImplementedError

    @property
    @abstractmethod
    def format(self) -> str:
        """The file format."""
        raise NotImplementedError

    __repr__ = _utils.dataclasses_no_defaults_repr

```

#### url

```python
url: str = url

```

The URL of the file.

#### force_download

```python
force_download: bool = force_download

```

For OpenAI and Google APIs it:

- If True, the file is downloaded and the data is sent to the model as bytes.
- If False, the URL is sent directly to the model and no download is performed.

#### vendor_metadata

```python
vendor_metadata: dict[str, Any] | None = vendor_metadata

```

Vendor-specific metadata for the file.

Supported by:

- `GoogleModel`: `VideoUrl.vendor_metadata` is used as `video_metadata`: https://ai.google.dev/gemini-api/docs/video-understanding#customize-video-processing
- `OpenAIChatModel`, `OpenAIResponsesModel`: `ImageUrl.vendor_metadata['detail']` is used as `detail` setting for images

#### media_type

```python
media_type: str

```

Return the media type of the file, based on the URL or the provided `media_type`.

#### identifier

```python
identifier: str

```

The identifier of the file, such as a unique ID.

This identifier can be provided to the model in a message to allow it to refer to this file in a tool call argument, and the tool can look up the file in question by iterating over the message history and finding the matching `FileUrl`.

This identifier is only automatically passed to the model when the `FileUrl` is returned by a tool. If you're passing the `FileUrl` as a user message, it's up to you to include a separate text part with the identifier, e.g. "This is file :" preceding the `FileUrl`.

It's also included in inline-text delimiters for providers that require inlining text documents, so the model can distinguish multiple files.

#### format

```python
format: str

```

The file format.
