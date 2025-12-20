### reduce_list_append

```python
reduce_list_append(
    current: list[T], inputs: T
) -> list[T]

```

A reducer that appends to a list.

Source code in `pydantic_graph/pydantic_graph/beta/join.py`

```python
def reduce_list_append(current: list[T], inputs: T) -> list[T]:
    """A reducer that appends to a list."""
    current.append(inputs)
    return current

```
