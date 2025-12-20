### DocumentUrl

Bases: `FileUrl`

The URL of the document.

Source code in `pydantic_ai_slim/pydantic_ai/messages.py`

```python
@dataclass(init=False, repr=False)
class DocumentUrl(FileUrl):
    """The URL of the document."""

    url: str
    """The URL of the document."""

    _: KW_ONLY

    kind: Literal['document-url'] = 'document-url'
    """Type identifier, this is available on all parts as a discriminator."""

    def __init__(
        self,
        url: str,
        *,
        media_type: str | None = None,
        identifier: str | None = None,
        force_download: bool = False,
        vendor_metadata: dict[str, Any] | None = None,
        kind: Literal['document-url'] = 'document-url',
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

    def _infer_media_type(self) -> str:
        """Return the media type of the document, based on the url."""
        # Common document types are hardcoded here as mime-type support for these
        # extensions varies across operating systems.
        if self.url.endswith(('.md', '.mdx', '.markdown')):
            return 'text/markdown'
        elif self.url.endswith('.asciidoc'):
            return 'text/x-asciidoc'
        elif self.url.endswith('.txt'):
            return 'text/plain'
        elif self.url.endswith('.pdf'):
            return 'application/pdf'
        elif self.url.endswith('.rtf'):
            return 'application/rtf'
        elif self.url.endswith('.doc'):
            return 'application/msword'
        elif self.url.endswith('.docx'):
            return 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        elif self.url.endswith('.xls'):
            return 'application/vnd.ms-excel'
        elif self.url.endswith('.xlsx'):
            return 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

        type_, _ = guess_type(self.url)
        if type_ is None:
            raise ValueError(
                f'Could not infer media type from document URL: {self.url}. Explicitly provide a `media_type` instead.'
            )
        return type_

    @property
    def format(self) -> DocumentFormat:
        """The file format of the document.

        The choice of supported formats were based on the Bedrock Converse API. Other APIs don't require to use a format.
        """
        media_type = self.media_type
        try:
            return _document_format_lookup[media_type]
        except KeyError as e:
            raise ValueError(f'Unknown document media type: {media_type}') from e

```

#### url

```python
url: str

```

The URL of the document.

#### kind

```python
kind: Literal['document-url'] = kind

```

Type identifier, this is available on all parts as a discriminator.

#### format

```python
format: DocumentFormat

```

The file format of the document.

The choice of supported formats were based on the Bedrock Converse API. Other APIs don't require to use a format.
