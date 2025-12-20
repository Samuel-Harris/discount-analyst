### FileWithUri

Bases: `TypedDict`

File with URI reference.

Source code in `.venv/lib/python3.12/site-packages/fasta2a/schema.py`

```python
@pydantic.with_config({'alias_generator': to_camel})
class FileWithUri(TypedDict):
    """File with URI reference."""

    uri: str
    """The URI of the file."""

    mime_type: NotRequired[str]
    """The mime type of the file."""

```

#### uri

```python
uri: str

```

The URI of the file.

#### mime_type

```python
mime_type: NotRequired[str]

```

The mime type of the file.
