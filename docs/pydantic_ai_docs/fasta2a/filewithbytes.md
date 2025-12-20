### FileWithBytes

Bases: `TypedDict`

File with base64 encoded data.

Source code in `.venv/lib/python3.12/site-packages/fasta2a/schema.py`

```python
@pydantic.with_config({'alias_generator': to_camel})
class FileWithBytes(TypedDict):
    """File with base64 encoded data."""

    bytes: str
    """The base64 encoded content of the file."""

    mime_type: NotRequired[str]
    """Optional mime type for the file."""

```

#### bytes

```python
bytes: str

```

The base64 encoded content of the file.

#### mime_type

```python
mime_type: NotRequired[str]

```

Optional mime type for the file.
