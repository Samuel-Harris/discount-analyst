### OpenIdConnectSecurityScheme

Bases: `TypedDict`

OpenID Connect security scheme.

Source code in `.venv/lib/python3.12/site-packages/fasta2a/schema.py`

```python
@pydantic.with_config({'alias_generator': to_camel})
class OpenIdConnectSecurityScheme(TypedDict):
    """OpenID Connect security scheme."""

    type: Literal['openIdConnect']
    open_id_connect_url: str
    """OpenId Connect URL to discover OAuth2 configuration values."""
    description: NotRequired[str]
    """Description of this security scheme."""

```

#### open_id_connect_url

```python
open_id_connect_url: str

```

OpenId Connect URL to discover OAuth2 configuration values.

#### description

```python
description: NotRequired[str]

```

Description of this security scheme.
