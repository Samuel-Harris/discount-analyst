### GraphRunResult

Bases: `Generic[StateT, RunEndT]`

The final result of running a graph.

Source code in `pydantic_graph/pydantic_graph/graph.py`

```python
@dataclass(init=False)
class GraphRunResult(Generic[StateT, RunEndT]):
    """The final result of running a graph."""

    output: RunEndT
    state: StateT
    persistence: BaseStatePersistence[StateT, RunEndT] = field(repr=False)

    def __init__(
        self,
        output: RunEndT,
        state: StateT,
        persistence: BaseStatePersistence[StateT, RunEndT],
        traceparent: str | None = None,
    ):
        self.output = output
        self.state = state
        self.persistence = persistence
        self.__traceparent = traceparent

    @overload
    def _traceparent(self, *, required: typing_extensions.Literal[False]) -> str | None: ...
    @overload
    def _traceparent(self) -> str: ...
    def _traceparent(self, *, required: bool = True) -> str | None:  # pragma: no cover
        if self.__traceparent is None and required:
            raise exceptions.GraphRuntimeError('No span was created for this graph run.')
        return self.__traceparent

```
