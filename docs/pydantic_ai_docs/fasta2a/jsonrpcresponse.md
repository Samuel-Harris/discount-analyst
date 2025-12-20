### JSONRPCResponse

Bases: `JSONRPCMessage`, `Generic[ResultT, ErrorT]`

A JSON RPC response.

Source code in `.venv/lib/python3.12/site-packages/fasta2a/schema.py`

```python
class JSONRPCResponse(JSONRPCMessage, Generic[ResultT, ErrorT]):
    """A JSON RPC response."""

    result: NotRequired[ResultT]
    error: NotRequired[ErrorT]

```
