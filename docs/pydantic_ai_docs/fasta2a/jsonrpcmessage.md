### JSONRPCMessage

Bases: `TypedDict`

A JSON RPC message.

Source code in `.venv/lib/python3.12/site-packages/fasta2a/schema.py`

```python
class JSONRPCMessage(TypedDict):
    """A JSON RPC message."""

    jsonrpc: Literal['2.0']
    """The JSON RPC version."""

    id: int | str | None
    """The request id."""

```

#### jsonrpc

```python
jsonrpc: Literal['2.0']

```

The JSON RPC version.

#### id

```python
id: int | str | None

```

The request id.
