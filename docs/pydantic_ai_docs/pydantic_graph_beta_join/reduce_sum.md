### reduce_sum

```python
reduce_sum(current: NumericT, inputs: NumericT) -> NumericT

```

A reducer that sums numbers.

Source code in `pydantic_graph/pydantic_graph/beta/join.py`

```python
def reduce_sum(current: NumericT, inputs: NumericT) -> NumericT:
    """A reducer that sums numbers."""
    return current + inputs

```
