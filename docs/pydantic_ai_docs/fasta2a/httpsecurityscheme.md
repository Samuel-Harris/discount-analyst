### HttpSecurityScheme

Bases: `TypedDict`

HTTP security scheme.

Source code in `.venv/lib/python3.12/site-packages/fasta2a/schema.py`

```python
@pydantic.with_config({'alias_generator': to_camel})
class HttpSecurityScheme(TypedDict):
    """HTTP security scheme."""

    type: Literal['http']
    scheme: str
    """The name of the HTTP Authorization scheme."""
    bearer_format: NotRequired[str]
    """A hint to the client to identify how the bearer token is formatted."""
    description: NotRequired[str]
    """Description of this security scheme."""

```

#### scheme

```python
scheme: str

```

The name of the HTTP Authorization scheme.

#### bearer_format

```python
bearer_format: NotRequired[str]

```

A hint to the client to identify how the bearer token is formatted.

#### description

```python
description: NotRequired[str]

```

Description of this security scheme.
