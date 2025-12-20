### AgentExtension

Bases: `TypedDict`

A declaration of an extension supported by an Agent.

Source code in `.venv/lib/python3.12/site-packages/fasta2a/schema.py`

```python
@pydantic.with_config({'alias_generator': to_camel})
class AgentExtension(TypedDict):
    """A declaration of an extension supported by an Agent."""

    uri: str
    """The URI of the extension."""

    description: NotRequired[str]
    """A description of how this agent uses this extension."""

    required: NotRequired[bool]
    """Whether the client must follow specific requirements of the extension."""

    params: NotRequired[dict[str, Any]]
    """Optional configuration for the extension."""

```

#### uri

```python
uri: str

```

The URI of the extension.

#### description

```python
description: NotRequired[str]

```

A description of how this agent uses this extension.

#### required

```python
required: NotRequired[bool]

```

Whether the client must follow specific requirements of the extension.

#### params

```python
params: NotRequired[dict[str, Any]]

```

Optional configuration for the extension.
