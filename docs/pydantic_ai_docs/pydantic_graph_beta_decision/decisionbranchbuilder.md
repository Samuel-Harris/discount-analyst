### DecisionBranchBuilder

Bases: `Generic[StateT, DepsT, OutputT, SourceT, HandledT]`

Builder for constructing decision branches with fluent API.

This builder provides methods to configure branches with destinations, forks, and transformations in a type-safe manner.

Instances of this class should be created using GraphBuilder.match, not created directly.

Source code in `pydantic_graph/pydantic_graph/beta/decision.py`

```python
@dataclass(init=False)
class DecisionBranchBuilder(Generic[StateT, DepsT, OutputT, SourceT, HandledT]):
    """Builder for constructing decision branches with fluent API.

    This builder provides methods to configure branches with destinations,
    forks, and transformations in a type-safe manner.

    Instances of this class should be created using [`GraphBuilder.match`][pydantic_graph.beta.graph_builder.GraphBuilder],
    not created directly.
    """

    _decision: Decision[StateT, DepsT, HandledT]
    """The parent decision node."""
    _source: TypeOrTypeExpression[SourceT]
    """The expected source type for this branch."""
    _matches: Callable[[Any], bool] | None
    """Optional matching predicate."""

    _path_builder: PathBuilder[StateT, DepsT, OutputT]
    """Builder for the execution path."""

    def __init__(
        self,
        *,
        decision: Decision[StateT, DepsT, HandledT],
        source: TypeOrTypeExpression[SourceT],
        matches: Callable[[Any], bool] | None,
        path_builder: PathBuilder[StateT, DepsT, OutputT],
    ):
        # This manually-defined initializer is necessary due to https://github.com/python/mypy/issues/17623.
        self._decision = decision
        self._source = source
        self._matches = matches
        self._path_builder = path_builder

    def to(
        self,
        destination: DestinationNode[StateT, DepsT, OutputT] | type[BaseNode[StateT, DepsT, Any]],
        /,
        *extra_destinations: DestinationNode[StateT, DepsT, OutputT] | type[BaseNode[StateT, DepsT, Any]],
        fork_id: str | None = None,
    ) -> DecisionBranch[SourceT]:
        """Set the destination(s) for this branch.

        Args:
            destination: The primary destination node.
            *extra_destinations: Additional destination nodes.
            fork_id: Optional node ID to use for the resulting broadcast fork if multiple destinations are provided.

        Returns:
            A completed DecisionBranch with the specified destinations.
        """
        destination = get_origin(destination) or destination
        extra_destinations = tuple(get_origin(d) or d for d in extra_destinations)
        destinations = [(NodeStep(d) if inspect.isclass(d) else d) for d in (destination, *extra_destinations)]
        return DecisionBranch(
            source=self._source,
            matches=self._matches,
            path=self._path_builder.to(*destinations, fork_id=fork_id),
            destinations=destinations,
        )

    def broadcast(
        self, get_forks: Callable[[Self], Sequence[DecisionBranch[SourceT]]], /, *, fork_id: str | None = None
    ) -> DecisionBranch[SourceT]:
        """Broadcast this decision branch into multiple destinations.

        Args:
            get_forks: The callback that will return a sequence of decision branches to broadcast to.
            fork_id: Optional node ID to use for the resulting broadcast fork.

        Returns:
            A completed DecisionBranch with the specified destinations.
        """
        fork_decision_branches = get_forks(self)
        new_paths = [b.path for b in fork_decision_branches]
        if not new_paths:
            raise GraphBuildingError(f'The call to {get_forks} returned no branches, but must return at least one.')
        path = self._path_builder.broadcast(new_paths, fork_id=fork_id)
        destinations = [d for fdp in fork_decision_branches for d in fdp.destinations]
        return DecisionBranch(source=self._source, matches=self._matches, path=path, destinations=destinations)

    def transform(
        self, func: TransformFunction[StateT, DepsT, OutputT, NewOutputT], /
    ) -> DecisionBranchBuilder[StateT, DepsT, NewOutputT, SourceT, HandledT]:
        """Apply a transformation to the branch's output.

        Args:
            func: Transformation function to apply.

        Returns:
            A new DecisionBranchBuilder where the provided transform is applied prior to generating the final output.
        """
        return DecisionBranchBuilder(
            decision=self._decision,
            source=self._source,
            matches=self._matches,
            path_builder=self._path_builder.transform(func),
        )

    def map(
        self: DecisionBranchBuilder[StateT, DepsT, Iterable[T], SourceT, HandledT]
        | DecisionBranchBuilder[StateT, DepsT, AsyncIterable[T], SourceT, HandledT],
        *,
        fork_id: str | None = None,
        downstream_join_id: str | None = None,
    ) -> DecisionBranchBuilder[StateT, DepsT, T, SourceT, HandledT]:
        """Spread the branch's output.

        To do this, the current output must be iterable, and any subsequent steps in the path being built for this
        branch will be applied to each item of the current output in parallel.

        Args:
            fork_id: Optional ID for the fork, defaults to a generated value
            downstream_join_id: Optional ID of a downstream join node which is involved when mapping empty iterables

        Returns:
            A new DecisionBranchBuilder where mapping is performed prior to generating the final output.
        """
        return DecisionBranchBuilder(
            decision=self._decision,
            source=self._source,
            matches=self._matches,
            path_builder=self._path_builder.map(fork_id=fork_id, downstream_join_id=downstream_join_id),
        )

    def label(self, label: str) -> DecisionBranchBuilder[StateT, DepsT, OutputT, SourceT, HandledT]:
        """Apply a label to the branch at the current point in the path being built.

        These labels are only used in generated mermaid diagrams.

        Args:
            label: The label to apply.

        Returns:
            A new DecisionBranchBuilder where the label has been applied at the end of the current path being built.
        """
        return DecisionBranchBuilder(
            decision=self._decision,
            source=self._source,
            matches=self._matches,
            path_builder=self._path_builder.label(label),
        )

```

#### to

```python
to(
    destination: (
        DestinationNode[StateT, DepsT, OutputT]
        | type[BaseNode[StateT, DepsT, Any]]
    ),
    /,
    *extra_destinations: DestinationNode[
        StateT, DepsT, OutputT
    ]
    | type[BaseNode[StateT, DepsT, Any]],
    fork_id: str | None = None,
) -> DecisionBranch[SourceT]

```

Set the destination(s) for this branch.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `destination` | `DestinationNode[StateT, DepsT, OutputT] | type[BaseNode[StateT, DepsT, Any]]` | The primary destination node. | _required_ | | `*extra_destinations` | `DestinationNode[StateT, DepsT, OutputT] | type[BaseNode[StateT, DepsT, Any]]` | Additional destination nodes. | `()` | | `fork_id` | `str | None` | Optional node ID to use for the resulting broadcast fork if multiple destinations are provided. | `None` |

Returns:

| Type | Description | | --- | --- | | `DecisionBranch[SourceT]` | A completed DecisionBranch with the specified destinations. |

Source code in `pydantic_graph/pydantic_graph/beta/decision.py`

```python
def to(
    self,
    destination: DestinationNode[StateT, DepsT, OutputT] | type[BaseNode[StateT, DepsT, Any]],
    /,
    *extra_destinations: DestinationNode[StateT, DepsT, OutputT] | type[BaseNode[StateT, DepsT, Any]],
    fork_id: str | None = None,
) -> DecisionBranch[SourceT]:
    """Set the destination(s) for this branch.

    Args:
        destination: The primary destination node.
        *extra_destinations: Additional destination nodes.
        fork_id: Optional node ID to use for the resulting broadcast fork if multiple destinations are provided.

    Returns:
        A completed DecisionBranch with the specified destinations.
    """
    destination = get_origin(destination) or destination
    extra_destinations = tuple(get_origin(d) or d for d in extra_destinations)
    destinations = [(NodeStep(d) if inspect.isclass(d) else d) for d in (destination, *extra_destinations)]
    return DecisionBranch(
        source=self._source,
        matches=self._matches,
        path=self._path_builder.to(*destinations, fork_id=fork_id),
        destinations=destinations,
    )

```

#### broadcast

```python
broadcast(
    get_forks: Callable[
        [Self], Sequence[DecisionBranch[SourceT]]
    ],
    /,
    *,
    fork_id: str | None = None,
) -> DecisionBranch[SourceT]

```

Broadcast this decision branch into multiple destinations.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `get_forks` | `Callable[[Self], Sequence[DecisionBranch[SourceT]]]` | The callback that will return a sequence of decision branches to broadcast to. | _required_ | | `fork_id` | `str | None` | Optional node ID to use for the resulting broadcast fork. | `None` |

Returns:

| Type | Description | | --- | --- | | `DecisionBranch[SourceT]` | A completed DecisionBranch with the specified destinations. |

Source code in `pydantic_graph/pydantic_graph/beta/decision.py`

```python
def broadcast(
    self, get_forks: Callable[[Self], Sequence[DecisionBranch[SourceT]]], /, *, fork_id: str | None = None
) -> DecisionBranch[SourceT]:
    """Broadcast this decision branch into multiple destinations.

    Args:
        get_forks: The callback that will return a sequence of decision branches to broadcast to.
        fork_id: Optional node ID to use for the resulting broadcast fork.

    Returns:
        A completed DecisionBranch with the specified destinations.
    """
    fork_decision_branches = get_forks(self)
    new_paths = [b.path for b in fork_decision_branches]
    if not new_paths:
        raise GraphBuildingError(f'The call to {get_forks} returned no branches, but must return at least one.')
    path = self._path_builder.broadcast(new_paths, fork_id=fork_id)
    destinations = [d for fdp in fork_decision_branches for d in fdp.destinations]
    return DecisionBranch(source=self._source, matches=self._matches, path=path, destinations=destinations)

```

#### transform

```python
transform(
    func: TransformFunction[
        StateT, DepsT, OutputT, NewOutputT
    ],
) -> DecisionBranchBuilder[
    StateT, DepsT, NewOutputT, SourceT, HandledT
]

```

Apply a transformation to the branch's output.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `func` | `TransformFunction[StateT, DepsT, OutputT, NewOutputT]` | Transformation function to apply. | _required_ |

Returns:

| Type | Description | | --- | --- | | `DecisionBranchBuilder[StateT, DepsT, NewOutputT, SourceT, HandledT]` | A new DecisionBranchBuilder where the provided transform is applied prior to generating the final output. |

Source code in `pydantic_graph/pydantic_graph/beta/decision.py`

```python
def transform(
    self, func: TransformFunction[StateT, DepsT, OutputT, NewOutputT], /
) -> DecisionBranchBuilder[StateT, DepsT, NewOutputT, SourceT, HandledT]:
    """Apply a transformation to the branch's output.

    Args:
        func: Transformation function to apply.

    Returns:
        A new DecisionBranchBuilder where the provided transform is applied prior to generating the final output.
    """
    return DecisionBranchBuilder(
        decision=self._decision,
        source=self._source,
        matches=self._matches,
        path_builder=self._path_builder.transform(func),
    )

```

#### map

```python
map(
    *,
    fork_id: str | None = None,
    downstream_join_id: str | None = None
) -> DecisionBranchBuilder[
    StateT, DepsT, T, SourceT, HandledT
]

```

Spread the branch's output.

To do this, the current output must be iterable, and any subsequent steps in the path being built for this branch will be applied to each item of the current output in parallel.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `fork_id` | `str | None` | Optional ID for the fork, defaults to a generated value | `None` | | `downstream_join_id` | `str | None` | Optional ID of a downstream join node which is involved when mapping empty iterables | `None` |

Returns:

| Type | Description | | --- | --- | | `DecisionBranchBuilder[StateT, DepsT, T, SourceT, HandledT]` | A new DecisionBranchBuilder where mapping is performed prior to generating the final output. |

Source code in `pydantic_graph/pydantic_graph/beta/decision.py`

```python
def map(
    self: DecisionBranchBuilder[StateT, DepsT, Iterable[T], SourceT, HandledT]
    | DecisionBranchBuilder[StateT, DepsT, AsyncIterable[T], SourceT, HandledT],
    *,
    fork_id: str | None = None,
    downstream_join_id: str | None = None,
) -> DecisionBranchBuilder[StateT, DepsT, T, SourceT, HandledT]:
    """Spread the branch's output.

    To do this, the current output must be iterable, and any subsequent steps in the path being built for this
    branch will be applied to each item of the current output in parallel.

    Args:
        fork_id: Optional ID for the fork, defaults to a generated value
        downstream_join_id: Optional ID of a downstream join node which is involved when mapping empty iterables

    Returns:
        A new DecisionBranchBuilder where mapping is performed prior to generating the final output.
    """
    return DecisionBranchBuilder(
        decision=self._decision,
        source=self._source,
        matches=self._matches,
        path_builder=self._path_builder.map(fork_id=fork_id, downstream_join_id=downstream_join_id),
    )

```

#### label

```python
label(
    label: str,
) -> DecisionBranchBuilder[
    StateT, DepsT, OutputT, SourceT, HandledT
]

```

Apply a label to the branch at the current point in the path being built.

These labels are only used in generated mermaid diagrams.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `label` | `str` | The label to apply. | _required_ |

Returns:

| Type | Description | | --- | --- | | `DecisionBranchBuilder[StateT, DepsT, OutputT, SourceT, HandledT]` | A new DecisionBranchBuilder where the label has been applied at the end of the current path being built. |

Source code in `pydantic_graph/pydantic_graph/beta/decision.py`

```python
def label(self, label: str) -> DecisionBranchBuilder[StateT, DepsT, OutputT, SourceT, HandledT]:
    """Apply a label to the branch at the current point in the path being built.

    These labels are only used in generated mermaid diagrams.

    Args:
        label: The label to apply.

    Returns:
        A new DecisionBranchBuilder where the label has been applied at the end of the current path being built.
    """
    return DecisionBranchBuilder(
        decision=self._decision,
        source=self._source,
        matches=self._matches,
        path_builder=self._path_builder.label(label),
    )

```
