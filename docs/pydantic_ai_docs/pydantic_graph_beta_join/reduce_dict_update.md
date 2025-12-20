### reduce_dict_update

```python
reduce_dict_update(
    current: dict[K, V], inputs: Mapping[K, V]
) -> dict[K, V]

```

A reducer that updates a dict.

Source code in `pydantic_graph/pydantic_graph/beta/join.py`

```python
def reduce_dict_update(current: dict[K, V], inputs: Mapping[K, V]) -> dict[K, V]:
    """A reducer that updates a dict."""
    current.update(inputs)
    return current

```
