### EndMarker

Bases: `Generic[OutputT]`

A marker indicating the end of graph execution with a final value.

EndMarker is used internally to signal that the graph has completed execution and carries the final output value.

Type Parameters

OutputT: The type of the final output value

Source code in `pydantic_graph/pydantic_graph/beta/graph.py`

```python
@dataclass(init=False)
class EndMarker(Generic[OutputT]):
    """A marker indicating the end of graph execution with a final value.

    EndMarker is used internally to signal that the graph has completed
    execution and carries the final output value.

    Type Parameters:
        OutputT: The type of the final output value
    """

    _value: OutputT
    """The final output value from the graph execution."""

    def __init__(self, value: OutputT):
        # This manually-defined initializer is necessary due to https://github.com/python/mypy/issues/17623.
        self._value = value

    @property
    def value(self) -> OutputT:
        return self._value

```
