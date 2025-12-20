### BinaryContent

Binary content, e.g. an audio or image file.

Source code in `pydantic_ai_slim/pydantic_ai/messages.py`

```python
@dataclass(init=False, repr=False)
class BinaryContent:
    """Binary content, e.g. an audio or image file."""

    data: bytes
    """The binary data."""

    _: KW_ONLY

    media_type: AudioMediaType | ImageMediaType | DocumentMediaType | str
    """The media type of the binary data."""

    vendor_metadata: dict[str, Any] | None = None
    """Vendor-specific metadata for the file.

    Supported by:
    - `GoogleModel`: `BinaryContent.vendor_metadata` is used as `video_metadata`: https://ai.google.dev/gemini-api/docs/video-understanding#customize-video-processing
    - `OpenAIChatModel`, `OpenAIResponsesModel`: `BinaryContent.vendor_metadata['detail']` is used as `detail` setting for images
    """

    _identifier: Annotated[str | None, pydantic.Field(alias='identifier', default=None, exclude=True)] = field(
        compare=False, default=None
    )

    kind: Literal['binary'] = 'binary'
    """Type identifier, this is available on all parts as a discriminator."""

    def __init__(
        self,
        data: bytes,
        *,
        media_type: AudioMediaType | ImageMediaType | DocumentMediaType | str,
        identifier: str | None = None,
        vendor_metadata: dict[str, Any] | None = None,
        kind: Literal['binary'] = 'binary',
        # Required for inline-snapshot which expects all dataclass `__init__` methods to take all field names as kwargs.
        _identifier: str | None = None,
    ) -> None:
        self.data = data
        self.media_type = media_type
        self._identifier = identifier or _identifier
        self.vendor_metadata = vendor_metadata
        self.kind = kind

    @staticmethod
    def narrow_type(bc: BinaryContent) -> BinaryContent | BinaryImage:
        """Narrow the type of the `BinaryContent` to `BinaryImage` if it's an image."""
        if bc.is_image:
            return BinaryImage(
                data=bc.data,
                media_type=bc.media_type,
                identifier=bc.identifier,
                vendor_metadata=bc.vendor_metadata,
            )
        else:
            return bc

    @classmethod
    def from_data_uri(cls, data_uri: str) -> BinaryContent:
        """Create a `BinaryContent` from a data URI."""
        prefix = 'data:'
        if not data_uri.startswith(prefix):
            raise ValueError('Data URI must start with "data:"')
        media_type, data = data_uri[len(prefix) :].split(';base64,', 1)
        return cls.narrow_type(cls(data=base64.b64decode(data), media_type=media_type))

    @classmethod
    def from_path(cls, path: PathLike[str]) -> BinaryContent:
        """Create a `BinaryContent` from a path.

        Defaults to 'application/octet-stream' if the media type cannot be inferred.

        Raises:
            FileNotFoundError: if the file does not exist.
            PermissionError: if the file cannot be read.
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f'File not found: {path}')
        media_type, _ = guess_type(path)
        if media_type is None:
            media_type = 'application/octet-stream'

        return cls.narrow_type(cls(data=path.read_bytes(), media_type=media_type))

    @pydantic.computed_field
    @property
    def identifier(self) -> str:
        """Identifier for the binary content, such as a unique ID.

        This identifier can be provided to the model in a message to allow it to refer to this file in a tool call argument,
        and the tool can look up the file in question by iterating over the message history and finding the matching `BinaryContent`.

        This identifier is only automatically passed to the model when the `BinaryContent` is returned by a tool.
        If you're passing the `BinaryContent` as a user message, it's up to you to include a separate text part with the identifier,
        e.g. "This is file <identifier>:" preceding the `BinaryContent`.

        It's also included in inline-text delimiters for providers that require inlining text documents, so the model can
        distinguish multiple files.
        """
        return self._identifier or _multi_modal_content_identifier(self.data)

    @property
    def data_uri(self) -> str:
        """Convert the `BinaryContent` to a data URI."""
        return f'data:{self.media_type};base64,{base64.b64encode(self.data).decode()}'

    @property
    def is_audio(self) -> bool:
        """Return `True` if the media type is an audio type."""
        return self.media_type.startswith('audio/')

    @property
    def is_image(self) -> bool:
        """Return `True` if the media type is an image type."""
        return self.media_type.startswith('image/')

    @property
    def is_video(self) -> bool:
        """Return `True` if the media type is a video type."""
        return self.media_type.startswith('video/')

    @property
    def is_document(self) -> bool:
        """Return `True` if the media type is a document type."""
        return self.media_type in _document_format_lookup

    @property
    def format(self) -> str:
        """The file format of the binary content."""
        try:
            if self.is_audio:
                return _audio_format_lookup[self.media_type]
            elif self.is_image:
                return _image_format_lookup[self.media_type]
            elif self.is_video:
                return _video_format_lookup[self.media_type]
            else:
                return _document_format_lookup[self.media_type]
        except KeyError as e:
            raise ValueError(f'Unknown media type: {self.media_type}') from e

    __repr__ = _utils.dataclasses_no_defaults_repr

```

#### data

```python
data: bytes = data

```

The binary data.

#### media_type

```python
media_type: (
    AudioMediaType
    | ImageMediaType
    | DocumentMediaType
    | str
) = media_type

```

The media type of the binary data.

#### vendor_metadata

```python
vendor_metadata: dict[str, Any] | None = vendor_metadata

```

Vendor-specific metadata for the file.

Supported by:

- `GoogleModel`: `BinaryContent.vendor_metadata` is used as `video_metadata`: https://ai.google.dev/gemini-api/docs/video-understanding#customize-video-processing
- `OpenAIChatModel`, `OpenAIResponsesModel`: `BinaryContent.vendor_metadata['detail']` is used as `detail` setting for images

#### kind

```python
kind: Literal['binary'] = kind

```

Type identifier, this is available on all parts as a discriminator.

#### narrow_type

```python
narrow_type(
    bc: BinaryContent,
) -> BinaryContent | BinaryImage

```

Narrow the type of the `BinaryContent` to `BinaryImage` if it's an image.

Source code in `pydantic_ai_slim/pydantic_ai/messages.py`

```python
@staticmethod
def narrow_type(bc: BinaryContent) -> BinaryContent | BinaryImage:
    """Narrow the type of the `BinaryContent` to `BinaryImage` if it's an image."""
    if bc.is_image:
        return BinaryImage(
            data=bc.data,
            media_type=bc.media_type,
            identifier=bc.identifier,
            vendor_metadata=bc.vendor_metadata,
        )
    else:
        return bc

```

#### from_data_uri

```python
from_data_uri(data_uri: str) -> BinaryContent

```

Create a `BinaryContent` from a data URI.

Source code in `pydantic_ai_slim/pydantic_ai/messages.py`

```python
@classmethod
def from_data_uri(cls, data_uri: str) -> BinaryContent:
    """Create a `BinaryContent` from a data URI."""
    prefix = 'data:'
    if not data_uri.startswith(prefix):
        raise ValueError('Data URI must start with "data:"')
    media_type, data = data_uri[len(prefix) :].split(';base64,', 1)
    return cls.narrow_type(cls(data=base64.b64decode(data), media_type=media_type))

```

#### from_path

```python
from_path(path: PathLike[str]) -> BinaryContent

```

Create a `BinaryContent` from a path.

Defaults to 'application/octet-stream' if the media type cannot be inferred.

Raises:

| Type | Description | | --- | --- | | `FileNotFoundError` | if the file does not exist. | | `PermissionError` | if the file cannot be read. |

Source code in `pydantic_ai_slim/pydantic_ai/messages.py`

```python
@classmethod
def from_path(cls, path: PathLike[str]) -> BinaryContent:
    """Create a `BinaryContent` from a path.

    Defaults to 'application/octet-stream' if the media type cannot be inferred.

    Raises:
        FileNotFoundError: if the file does not exist.
        PermissionError: if the file cannot be read.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f'File not found: {path}')
    media_type, _ = guess_type(path)
    if media_type is None:
        media_type = 'application/octet-stream'

    return cls.narrow_type(cls(data=path.read_bytes(), media_type=media_type))

```

#### identifier

```python
identifier: str

```

Identifier for the binary content, such as a unique ID.

This identifier can be provided to the model in a message to allow it to refer to this file in a tool call argument, and the tool can look up the file in question by iterating over the message history and finding the matching `BinaryContent`.

This identifier is only automatically passed to the model when the `BinaryContent` is returned by a tool. If you're passing the `BinaryContent` as a user message, it's up to you to include a separate text part with the identifier, e.g. "This is file :" preceding the `BinaryContent`.

It's also included in inline-text delimiters for providers that require inlining text documents, so the model can distinguish multiple files.

#### data_uri

```python
data_uri: str

```

Convert the `BinaryContent` to a data URI.

#### is_audio

```python
is_audio: bool

```

Return `True` if the media type is an audio type.

#### is_image

```python
is_image: bool

```

Return `True` if the media type is an image type.

#### is_video

```python
is_video: bool

```

Return `True` if the media type is a video type.

#### is_document

```python
is_document: bool

```

Return `True` if the media type is a document type.

#### format

```python
format: str

```

The file format of the binary content.
