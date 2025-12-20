### AgentInterface

Bases: `TypedDict`

An interface that the agent supports.

Source code in `.venv/lib/python3.12/site-packages/fasta2a/schema.py`

```python
@pydantic.with_config({'alias_generator': to_camel})
class AgentInterface(TypedDict):
    """An interface that the agent supports."""

    transport: str
    """The transport protocol (e.g., 'jsonrpc', 'websocket')."""

    url: str
    """The URL endpoint for this transport."""

    description: NotRequired[str]
    """Description of this interface."""

```

#### transport

```python
transport: str

```

The transport protocol (e.g., 'jsonrpc', 'websocket').

#### url

```python
url: str

```

The URL endpoint for this transport.

#### description

```python
description: NotRequired[str]

```

Description of this interface.
