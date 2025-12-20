### Decision

Bases: `Generic[StateT, DepsT, HandledT]`

Decision node for conditional branching in graph execution.

A Decision node evaluates conditions and routes execution to different branches based on the input data type or custom matching logic.

Source code in `pydantic_graph/pydantic_graph/beta/decision.py`

```python
@dataclass(kw_only=True)
class Decision(Generic[StateT, DepsT, HandledT]):
    """Decision node for conditional branching in graph execution.

    A Decision node evaluates conditions and routes execution to different
    branches based on the input data type or custom matching logic.
    """

    id: NodeID
    """Unique identifier for this decision node."""

    branches: list[DecisionBranch[Any]]
    """List of branches that can be taken from this decision."""

    note: str | None
    """Optional documentation note for this decision."""

    def branch(self, branch: DecisionBranch[T]) -> Decision[StateT, DepsT, HandledT | T]:
        """Add a new branch to this decision.

        Args:
            branch: The branch to add to this decision.

        Returns:
            A new Decision with the additional branch.
        """
        return Decision(id=self.id, branches=self.branches + [branch], note=self.note)

    def _force_handled_contravariant(self, inputs: HandledT) -> Never:  # pragma: no cover
        """Forces this type to be contravariant in the HandledT type variable.

        This is an implementation detail of how we can type-check that all possible input types have
        been exhaustively covered.

        Args:
            inputs: Input data of handled types.

        Raises:
            RuntimeError: Always, as this method should never be executed.
        """
        raise RuntimeError('This method should never be called, it is just defined for typing purposes.')

```

#### id

```python
id: NodeID

```

Unique identifier for this decision node.

#### branches

```python
branches: list[DecisionBranch[Any]]

```

List of branches that can be taken from this decision.

#### note

```python
note: str | None

```

Optional documentation note for this decision.

#### branch

```python
branch(
    branch: DecisionBranch[T],
) -> Decision[StateT, DepsT, HandledT | T]

```

Add a new branch to this decision.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `branch` | `DecisionBranch[T]` | The branch to add to this decision. | _required_ |

Returns:

| Type | Description | | --- | --- | | `Decision[StateT, DepsT, HandledT | T]` | A new Decision with the additional branch. |

Source code in `pydantic_graph/pydantic_graph/beta/decision.py`

```python
def branch(self, branch: DecisionBranch[T]) -> Decision[StateT, DepsT, HandledT | T]:
    """Add a new branch to this decision.

    Args:
        branch: The branch to add to this decision.

    Returns:
        A new Decision with the additional branch.
    """
    return Decision(id=self.id, branches=self.branches + [branch], note=self.note)

```
