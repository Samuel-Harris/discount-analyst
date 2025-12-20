### ACIToolset

Bases: `FunctionToolset`

A toolset that wraps ACI.dev tools.

Source code in `pydantic_ai_slim/pydantic_ai/ext/aci.py`

```python
class ACIToolset(FunctionToolset):
    """A toolset that wraps ACI.dev tools."""

    def __init__(self, aci_functions: Sequence[str], linked_account_owner_id: str, *, id: str | None = None):
        super().__init__(
            [tool_from_aci(aci_function, linked_account_owner_id) for aci_function in aci_functions], id=id
        )

```
