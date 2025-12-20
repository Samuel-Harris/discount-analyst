### reduce_list_extend

```python
reduce_list_extend(
    current: list[T], inputs: Iterable[T]
) -> list[T]

```

A reducer that extends a list.

Source code in `pydantic_graph/pydantic_graph/beta/join.py`

```python
def reduce_list_extend(current: list[T], inputs: Iterable[T]) -> list[T]:
    """A reducer that extends a list."""
    current.extend(inputs)
    return current

```
