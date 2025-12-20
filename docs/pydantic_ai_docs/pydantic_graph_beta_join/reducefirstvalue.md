### ReduceFirstValue

Bases: `Generic[T]`

A reducer that returns the first value it encounters, and cancels all other tasks.

Source code in `pydantic_graph/pydantic_graph/beta/join.py`

```python
@dataclass
class ReduceFirstValue(Generic[T]):
    """A reducer that returns the first value it encounters, and cancels all other tasks."""

    def __call__(self, ctx: ReducerContext[object, object], current: T, inputs: T) -> T:
        """The reducer function."""
        ctx.cancel_sibling_tasks()
        return inputs

```

#### **call**

```python
__call__(
    ctx: ReducerContext[object, object],
    current: T,
    inputs: T,
) -> T

```

The reducer function.

Source code in `pydantic_graph/pydantic_graph/beta/join.py`

```python
def __call__(self, ctx: ReducerContext[object, object], current: T, inputs: T) -> T:
    """The reducer function."""
    ctx.cancel_sibling_tasks()
    return inputs

```
