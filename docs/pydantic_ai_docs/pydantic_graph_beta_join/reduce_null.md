### reduce_null

```python
reduce_null(current: None, inputs: Any) -> None

```

A reducer that discards all input data and returns None.

Source code in `pydantic_graph/pydantic_graph/beta/join.py`

```python
def reduce_null(current: None, inputs: Any) -> None:
    """A reducer that discards all input data and returns None."""
    return None

```
