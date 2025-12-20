### JSONRPCError

Bases: `TypedDict`, `Generic[CodeT, MessageT]`

A JSON RPC error.

Source code in `.venv/lib/python3.12/site-packages/fasta2a/schema.py`

```python
class JSONRPCError(TypedDict, Generic[CodeT, MessageT]):
    """A JSON RPC error."""

    code: CodeT
    message: MessageT
    data: NotRequired[Any]

```
