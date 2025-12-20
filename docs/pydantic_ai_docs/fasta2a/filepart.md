### FilePart

Bases: `_BasePart`

A part that contains a file.

Source code in `.venv/lib/python3.12/site-packages/fasta2a/schema.py`

```python
@pydantic.with_config({'alias_generator': to_camel})
class FilePart(_BasePart):
    """A part that contains a file."""

    kind: Literal['file']
    """The kind of the part."""

    file: FileWithBytes | FileWithUri
    """The file content - either bytes or URI."""

```

#### kind

```python
kind: Literal['file']

```

The kind of the part.

#### file

```python
file: FileWithBytes | FileWithUri

```

The file content - either bytes or URI.
