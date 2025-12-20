### DataPart

Bases: `_BasePart`

A part that contains structured data.

Source code in `.venv/lib/python3.12/site-packages/fasta2a/schema.py`

```python
@pydantic.with_config({'alias_generator': to_camel})
class DataPart(_BasePart):
    """A part that contains structured data."""

    kind: Literal['data']
    """The kind of the part."""

    data: dict[str, Any]
    """The data of the part."""

```

#### kind

```python
kind: Literal['data']

```

The kind of the part.

#### data

```python
data: dict[str, Any]

```

The data of the part.
