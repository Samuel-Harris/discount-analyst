### SupportsSum

Bases: `Protocol`

A protocol for a type that supports adding to itself.

Source code in `pydantic_graph/pydantic_graph/beta/join.py`

```python
class SupportsSum(Protocol):
    """A protocol for a type that supports adding to itself."""

    @abstractmethod
    def __add__(self, other: Self, /) -> Self:
        pass

```
