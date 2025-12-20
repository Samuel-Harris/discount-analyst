### End

Bases: `Generic[RunEndT]`

Type to return from a node to signal the end of the graph.

Source code in `pydantic_graph/pydantic_graph/nodes.py`

```python
@dataclass
class End(Generic[RunEndT]):
    """Type to return from a node to signal the end of the graph."""

    data: RunEndT
    """Data to return from the graph."""

    def deep_copy_data(self) -> End[RunEndT]:
        """Returns a deep copy of the end of the run."""
        if self.data is None:
            return self
        else:
            end = End(copy.deepcopy(self.data))
            end.set_snapshot_id(self.get_snapshot_id())
            return end

    def get_snapshot_id(self) -> str:
        if snapshot_id := getattr(self, '__snapshot_id', None):
            return snapshot_id
        else:
            self.__dict__['__snapshot_id'] = snapshot_id = generate_snapshot_id('end')
            return snapshot_id

    def set_snapshot_id(self, set_id: str) -> None:
        self.__dict__['__snapshot_id'] = set_id

```

#### data

```python
data: RunEndT

```

Data to return from the graph.

#### deep_copy_data

```python
deep_copy_data() -> End[RunEndT]

```

Returns a deep copy of the end of the run.

Source code in `pydantic_graph/pydantic_graph/nodes.py`

```python
def deep_copy_data(self) -> End[RunEndT]:
    """Returns a deep copy of the end of the run."""
    if self.data is None:
        return self
    else:
        end = End(copy.deepcopy(self.data))
        end.set_snapshot_id(self.get_snapshot_id())
        return end

```
