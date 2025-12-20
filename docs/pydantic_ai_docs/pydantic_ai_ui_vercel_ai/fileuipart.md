### FileUIPart

Bases: `BaseUIPart`

A file part of a message.

Source code in `pydantic_ai_slim/pydantic_ai/ui/vercel_ai/request_types.py`

```python
class FileUIPart(BaseUIPart):
    """A file part of a message."""

    type: Literal['file'] = 'file'

    media_type: str
    """
    IANA media type of the file.
    @see https://www.iana.org/assignments/media-types/media-types.xhtml
    """

    filename: str | None = None
    """Optional filename of the file."""

    url: str
    """
    The URL of the file.
    It can either be a URL to a hosted file or a [Data URL](https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/Data_URLs).
    """

    provider_metadata: ProviderMetadata | None = None
    """The provider metadata."""

```

#### media_type

```python
media_type: str

```

IANA media type of the file. @see https://www.iana.org/assignments/media-types/media-types.xhtml

#### filename

```python
filename: str | None = None

```

Optional filename of the file.

#### url

```python
url: str

```

The URL of the file. It can either be a URL to a hosted file or a [Data URL](https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/Data_URLs).

#### provider_metadata

```python
provider_metadata: ProviderMetadata | None = None

```

The provider metadata.
