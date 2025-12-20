### OAuth2SecurityScheme

Bases: `TypedDict`

OAuth2 security scheme.

Source code in `.venv/lib/python3.12/site-packages/fasta2a/schema.py`

```python
@pydantic.with_config({'alias_generator': to_camel})
class OAuth2SecurityScheme(TypedDict):
    """OAuth2 security scheme."""

    type: Literal['oauth2']
    flows: dict[str, Any]
    """An object containing configuration information for the flow types supported."""
    description: NotRequired[str]
    """Description of this security scheme."""

```

#### flows

```python
flows: dict[str, Any]

```

An object containing configuration information for the flow types supported.

#### description

```python
description: NotRequired[str]

```

Description of this security scheme.
