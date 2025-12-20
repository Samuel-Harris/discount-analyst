### DecisionBranch

Bases: `Generic[SourceT]`

Represents a single branch within a decision node.

Each branch defines the conditions under which it should be taken and the path to follow when those conditions are met.

Note: with the current design, it is actually _critical_ that this class is invariant in SourceT for the sake of type-checking that inputs to a Decision are actually handled. See the `# type: ignore` comment in `tests.graph.beta.test_graph_edge_cases.test_decision_no_matching_branch` for an example of how this works.

Source code in `pydantic_graph/pydantic_graph/beta/decision.py`

```python
@dataclass
class DecisionBranch(Generic[SourceT]):
    """Represents a single branch within a decision node.

    Each branch defines the conditions under which it should be taken
    and the path to follow when those conditions are met.

    Note: with the current design, it is actually _critical_ that this class is invariant in SourceT for the sake
    of type-checking that inputs to a Decision are actually handled. See the `# type: ignore` comment in
    `tests.graph.beta.test_graph_edge_cases.test_decision_no_matching_branch` for an example of how this works.
    """

    source: TypeOrTypeExpression[SourceT]
    """The expected type of data for this branch.

    This is necessary for exhaustiveness-checking when handling the inputs to a decision node."""

    matches: Callable[[Any], bool] | None
    """An optional predicate function used to determine whether input data matches this branch.

    If `None`, default logic is used which attempts to check the value for type-compatibility with the `source` type:
    * If `source` is `Any` or `object`, the branch will always match
    * If `source` is a `Literal` type, this branch will match if the value is one of the parametrizing literal values
    * If `source` is any other type, the value will be checked for matching using `isinstance`

    Inputs are tested against each branch of a decision node in order, and the path of the first matching branch is
    used to handle the input value.
    """

    path: Path
    """The execution path to follow when an input value matches this branch of a decision node.

    This can include transforming, mapping, and broadcasting the output before sending to the next node or nodes.

    The path can also include position-aware labels which are used when generating mermaid diagrams."""

    destinations: list[AnyDestinationNode]
    """The destination nodes that can be referenced by DestinationMarker in the path."""

```

#### source

```python
source: TypeOrTypeExpression[SourceT]

```

The expected type of data for this branch.

This is necessary for exhaustiveness-checking when handling the inputs to a decision node.

#### matches

```python
matches: Callable[[Any], bool] | None

```

An optional predicate function used to determine whether input data matches this branch.

If `None`, default logic is used which attempts to check the value for type-compatibility with the `source` type: _ If `source` is `Any` or `object`, the branch will always match _ If `source` is a `Literal` type, this branch will match if the value is one of the parametrizing literal values \* If `source` is any other type, the value will be checked for matching using `isinstance`

Inputs are tested against each branch of a decision node in order, and the path of the first matching branch is used to handle the input value.

#### path

```python
path: Path

```

The execution path to follow when an input value matches this branch of a decision node.

This can include transforming, mapping, and broadcasting the output before sending to the next node or nodes.

The path can also include position-aware labels which are used when generating mermaid diagrams.

#### destinations

```python
destinations: list[AnyDestinationNode]

```

The destination nodes that can be referenced by DestinationMarker in the path.
