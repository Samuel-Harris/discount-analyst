### ApiKeySecurityScheme

Bases: `TypedDict`

API Key security scheme.

Source code in `.venv/lib/python3.12/site-packages/fasta2a/schema.py`

```python
@pydantic.with_config({'alias_generator': to_camel})
class ApiKeySecurityScheme(TypedDict):
    """API Key security scheme."""

    type: Literal['apiKey']
    name: str
    """The name of the header, query or cookie parameter to be used."""
    in_: Literal['query', 'header', 'cookie']
    """The location of the API key."""
    description: NotRequired[str]
    """Description of this security scheme."""

```

#### name

```python
name: str

```

The name of the header, query or cookie parameter to be used.

#### in\_

```python
in_: Literal['query', 'header', 'cookie']

```

The location of the API key.

#### description

```python
description: NotRequired[str]

```

Description of this security scheme.
