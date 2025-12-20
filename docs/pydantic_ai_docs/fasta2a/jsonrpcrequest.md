### JSONRPCRequest

Bases: `JSONRPCMessage`, `Generic[Method, Params]`

A JSON RPC request.

Source code in `.venv/lib/python3.12/site-packages/fasta2a/schema.py`

```python
class JSONRPCRequest(JSONRPCMessage, Generic[Method, Params]):
    """A JSON RPC request."""

    method: Method
    """The method to call."""

    params: Params
    """The parameters to pass to the method."""

```

#### method

```python
method: Method

```

The method to call.

#### params

```python
params: Params

```

The parameters to pass to the method.
