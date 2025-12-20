### TextPart

Bases: `_BasePart`

A part that contains text.

Source code in `.venv/lib/python3.12/site-packages/fasta2a/schema.py`

```python
@pydantic.with_config({'alias_generator': to_camel})
class TextPart(_BasePart):
    """A part that contains text."""

    kind: Literal['text']
    """The kind of the part."""

    text: str
    """The text of the part."""

```

#### kind

```python
kind: Literal['text']

```

The kind of the part.

#### text

```python
text: str

```

The text of the part.
