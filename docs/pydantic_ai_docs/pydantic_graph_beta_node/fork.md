### Fork

Bases: `Generic[InputT, OutputT]`

Fork node that creates parallel execution branches.

A Fork node splits the execution flow into multiple parallel branches, enabling concurrent execution of downstream nodes. It can either map a sequence across multiple branches or duplicate data to each branch.

Source code in `pydantic_graph/pydantic_graph/beta/node.py`

```python
@dataclass
class Fork(Generic[InputT, OutputT]):
    """Fork node that creates parallel execution branches.

    A Fork node splits the execution flow into multiple parallel branches,
    enabling concurrent execution of downstream nodes. It can either map
    a sequence across multiple branches or duplicate data to each branch.
    """

    id: ForkID
    """Unique identifier for this fork node."""

    is_map: bool
    """Determines fork behavior.

    If True, InputT must be Sequence[OutputT] and each element is sent to a separate branch.
    If False, InputT must be OutputT and the same data is sent to all branches.
    """
    downstream_join_id: JoinID | None
    """Optional identifier of a downstream join node that should be jumped to if mapping an empty iterable."""

    def _force_variance(self, inputs: InputT) -> OutputT:  # pragma: no cover
        """Force type variance for proper generic typing.

        This method exists solely for type checking purposes and should never be called.

        Args:
            inputs: Input data to be forked.

        Returns:
            Output data type (never actually returned).

        Raises:
            RuntimeError: Always, as this method should never be executed.
        """
        raise RuntimeError('This method should never be called, it is just defined for typing purposes.')

```

#### id

```python
id: ForkID

```

Unique identifier for this fork node.

#### is_map

```python
is_map: bool

```

Determines fork behavior.

If True, InputT must be Sequence[OutputT] and each element is sent to a separate branch. If False, InputT must be OutputT and the same data is sent to all branches.

#### downstream_join_id

```python
downstream_join_id: JoinID | None

```

Optional identifier of a downstream join node that should be jumped to if mapping an empty iterable.
