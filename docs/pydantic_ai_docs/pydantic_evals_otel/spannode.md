### SpanNode

A node in the span tree; provides references to parents/children for easy traversal and queries.

Source code in `pydantic_evals/pydantic_evals/otel/span_tree.py`

```python
@dataclass(repr=False, kw_only=True)
class SpanNode:
    """A node in the span tree; provides references to parents/children for easy traversal and queries."""

    name: str
    trace_id: int
    span_id: int
    parent_span_id: int | None
    start_timestamp: datetime
    end_timestamp: datetime
    attributes: dict[str, AttributeValue]

    @property
    def duration(self) -> timedelta:
        """Return the span's duration as a timedelta, or None if start/end not set."""
        return self.end_timestamp - self.start_timestamp

    @property
    def children(self) -> list[SpanNode]:
        return list(self.children_by_id.values())

    @property
    def descendants(self) -> list[SpanNode]:
        """Return all descendants of this node in DFS order."""
        return self.find_descendants(lambda _: True)

    @property
    def ancestors(self) -> list[SpanNode]:
        """Return all ancestors of this node."""
        return self.find_ancestors(lambda _: True)

    @property
    def node_key(self) -> str:
        return f'{self.trace_id:032x}:{self.span_id:016x}'

    @property
    def parent_node_key(self) -> str | None:
        return None if self.parent_span_id is None else f'{self.trace_id:032x}:{self.parent_span_id:016x}'

    # -------------------------------------------------------------------------
    # Construction
    # -------------------------------------------------------------------------
    def __post_init__(self):
        self.parent: SpanNode | None = None
        self.children_by_id: dict[str, SpanNode] = {}

    @staticmethod
    def from_readable_span(span: ReadableSpan) -> SpanNode:
        assert span.context is not None, 'Span has no context'
        assert span.start_time is not None, 'Span has no start time'
        assert span.end_time is not None, 'Span has no end time'
        return SpanNode(
            name=span.name,
            trace_id=span.context.trace_id,
            span_id=span.context.span_id,
            parent_span_id=span.parent.span_id if span.parent else None,
            start_timestamp=datetime.fromtimestamp(span.start_time / 1e9, tz=timezone.utc),
            end_timestamp=datetime.fromtimestamp(span.end_time / 1e9, tz=timezone.utc),
            attributes=dict(span.attributes or {}),
        )

    def add_child(self, child: SpanNode) -> None:
        """Attach a child node to this node's list of children."""
        assert child.trace_id == self.trace_id, f"traces don't match: {child.trace_id:032x} != {self.trace_id:032x}"
        assert child.parent_span_id == self.span_id, (
            f'parent span mismatch: {child.parent_span_id:016x} != {self.span_id:016x}'
        )
        self.children_by_id[child.node_key] = child
        child.parent = self

    # -------------------------------------------------------------------------
    # Child queries
    # -------------------------------------------------------------------------
    def find_children(self, predicate: SpanQuery | SpanPredicate) -> list[SpanNode]:
        """Return all immediate children that satisfy the given predicate."""
        return list(self._filter_children(predicate))

    def first_child(self, predicate: SpanQuery | SpanPredicate) -> SpanNode | None:
        """Return the first immediate child that satisfies the given predicate, or None if none match."""
        return next(self._filter_children(predicate), None)

    def any_child(self, predicate: SpanQuery | SpanPredicate) -> bool:
        """Returns True if there is at least one child that satisfies the predicate."""
        return self.first_child(predicate) is not None

    def _filter_children(self, predicate: SpanQuery | SpanPredicate) -> Iterator[SpanNode]:
        return (child for child in self.children if child.matches(predicate))

    # -------------------------------------------------------------------------
    # Descendant queries (DFS)
    # -------------------------------------------------------------------------
    def find_descendants(
        self, predicate: SpanQuery | SpanPredicate, stop_recursing_when: SpanQuery | SpanPredicate | None = None
    ) -> list[SpanNode]:
        """Return all descendant nodes that satisfy the given predicate in DFS order."""
        return list(self._filter_descendants(predicate, stop_recursing_when))

    def first_descendant(
        self, predicate: SpanQuery | SpanPredicate, stop_recursing_when: SpanQuery | SpanPredicate | None = None
    ) -> SpanNode | None:
        """DFS: Return the first descendant (in DFS order) that satisfies the given predicate, or `None` if none match."""
        return next(self._filter_descendants(predicate, stop_recursing_when), None)

    def any_descendant(
        self, predicate: SpanQuery | SpanPredicate, stop_recursing_when: SpanQuery | SpanPredicate | None = None
    ) -> bool:
        """Returns `True` if there is at least one descendant that satisfies the predicate."""
        return self.first_descendant(predicate, stop_recursing_when) is not None

    def _filter_descendants(
        self, predicate: SpanQuery | SpanPredicate, stop_recursing_when: SpanQuery | SpanPredicate | None
    ) -> Iterator[SpanNode]:
        stack = list(self.children)
        while stack:
            node = stack.pop()
            if node.matches(predicate):
                yield node
            if stop_recursing_when is not None and node.matches(stop_recursing_when):
                continue
            stack.extend(node.children)

    # -------------------------------------------------------------------------
    # Ancestor queries (DFS "up" the chain)
    # -------------------------------------------------------------------------
    def find_ancestors(
        self, predicate: SpanQuery | SpanPredicate, stop_recursing_when: SpanQuery | SpanPredicate | None = None
    ) -> list[SpanNode]:
        """Return all ancestors that satisfy the given predicate."""
        return list(self._filter_ancestors(predicate, stop_recursing_when))

    def first_ancestor(
        self, predicate: SpanQuery | SpanPredicate, stop_recursing_when: SpanQuery | SpanPredicate | None = None
    ) -> SpanNode | None:
        """Return the closest ancestor that satisfies the given predicate, or `None` if none match."""
        return next(self._filter_ancestors(predicate, stop_recursing_when), None)

    def any_ancestor(
        self, predicate: SpanQuery | SpanPredicate, stop_recursing_when: SpanQuery | SpanPredicate | None = None
    ) -> bool:
        """Returns True if any ancestor satisfies the predicate."""
        return self.first_ancestor(predicate, stop_recursing_when) is not None

    def _filter_ancestors(
        self, predicate: SpanQuery | SpanPredicate, stop_recursing_when: SpanQuery | SpanPredicate | None
    ) -> Iterator[SpanNode]:
        node = self.parent
        while node:
            if node.matches(predicate):
                yield node
            if stop_recursing_when is not None and node.matches(stop_recursing_when):
                break
            node = node.parent

    # -------------------------------------------------------------------------
    # Query matching
    # -------------------------------------------------------------------------
    def matches(self, query: SpanQuery | SpanPredicate) -> bool:
        """Check if the span node matches the query conditions or predicate."""
        if callable(query):
            return query(self)

        return self._matches_query(query)

    def _matches_query(self, query: SpanQuery) -> bool:  # noqa: C901
        """Check if the span matches the query conditions."""
        # Logical combinations
        if or_ := query.get('or_'):
            if len(query) > 1:
                raise ValueError("Cannot combine 'or_' conditions with other conditions at the same level")
            return any(self._matches_query(q) for q in or_)
        if not_ := query.get('not_'):
            if self._matches_query(not_):
                return False
        if and_ := query.get('and_'):
            results = [self._matches_query(q) for q in and_]
            if not all(results):
                return False
        # At this point, all existing ANDs and no existing ORs have passed, so it comes down to this condition

        # Name conditions
        if (name_equals := query.get('name_equals')) and self.name != name_equals:
            return False
        if (name_contains := query.get('name_contains')) and name_contains not in self.name:
            return False
        if (name_matches_regex := query.get('name_matches_regex')) and not re.match(name_matches_regex, self.name):
            return False

        # Attribute conditions
        if (has_attributes := query.get('has_attributes')) and not all(
            self.attributes.get(key) == value for key, value in has_attributes.items()
        ):
            return False
        if (has_attributes_keys := query.get('has_attribute_keys')) and not all(
            key in self.attributes for key in has_attributes_keys
        ):
            return False

        # Timing conditions
        if (min_duration := query.get('min_duration')) is not None:
            if not isinstance(min_duration, timedelta):
                min_duration = timedelta(seconds=min_duration)
            if self.duration < min_duration:
                return False
        if (max_duration := query.get('max_duration')) is not None:
            if not isinstance(max_duration, timedelta):
                max_duration = timedelta(seconds=max_duration)
            if self.duration > max_duration:
                return False

        # Children conditions
        if (min_child_count := query.get('min_child_count')) and len(self.children) < min_child_count:
            return False
        if (max_child_count := query.get('max_child_count')) and len(self.children) > max_child_count:
            return False
        if (some_child_has := query.get('some_child_has')) and not any(
            child._matches_query(some_child_has) for child in self.children
        ):
            return False
        if (all_children_have := query.get('all_children_have')) and not all(
            child._matches_query(all_children_have) for child in self.children
        ):
            return False
        if (no_child_has := query.get('no_child_has')) and any(
            child._matches_query(no_child_has) for child in self.children
        ):
            return False

        # Descendant conditions
        # The following local functions with cache decorators are used to avoid repeatedly evaluating these properties
        @cache
        def descendants():
            return self.descendants

        @cache
        def pruned_descendants():
            stop_recursing_when = query.get('stop_recursing_when')
            return (
                self._filter_descendants(lambda _: True, stop_recursing_when) if stop_recursing_when else descendants()
            )

        if (min_descendant_count := query.get('min_descendant_count')) and len(descendants()) < min_descendant_count:
            return False
        if (max_descendant_count := query.get('max_descendant_count')) and len(descendants()) > max_descendant_count:
            return False
        if (some_descendant_has := query.get('some_descendant_has')) and not any(
            descendant._matches_query(some_descendant_has) for descendant in pruned_descendants()
        ):
            return False
        if (all_descendants_have := query.get('all_descendants_have')) and not all(
            descendant._matches_query(all_descendants_have) for descendant in pruned_descendants()
        ):
            return False
        if (no_descendant_has := query.get('no_descendant_has')) and any(
            descendant._matches_query(no_descendant_has) for descendant in pruned_descendants()
        ):
            return False

        # Ancestor conditions
        # The following local functions with cache decorators are used to avoid repeatedly evaluating these properties
        @cache
        def ancestors():
            return self.ancestors

        @cache
        def pruned_ancestors():
            stop_recursing_when = query.get('stop_recursing_when')
            return self._filter_ancestors(lambda _: True, stop_recursing_when) if stop_recursing_when else ancestors()

        if (min_depth := query.get('min_depth')) and len(ancestors()) < min_depth:
            return False
        if (max_depth := query.get('max_depth')) and len(ancestors()) > max_depth:
            return False
        if (some_ancestor_has := query.get('some_ancestor_has')) and not any(
            ancestor._matches_query(some_ancestor_has) for ancestor in pruned_ancestors()
        ):
            return False
        if (all_ancestors_have := query.get('all_ancestors_have')) and not all(
            ancestor._matches_query(all_ancestors_have) for ancestor in pruned_ancestors()
        ):
            return False
        if (no_ancestor_has := query.get('no_ancestor_has')) and any(
            ancestor._matches_query(no_ancestor_has) for ancestor in pruned_ancestors()
        ):
            return False

        return True

    # -------------------------------------------------------------------------
    # String representation
    # -------------------------------------------------------------------------
    def repr_xml(
        self,
        include_children: bool = True,
        include_trace_id: bool = False,
        include_span_id: bool = False,
        include_start_timestamp: bool = False,
        include_duration: bool = False,
    ) -> str:
        """Return an XML-like string representation of the node.

        Optionally includes children, trace_id, span_id, start_timestamp, and duration.
        """
        first_line_parts = [f'<SpanNode name={self.name!r}']
        if include_trace_id:
            first_line_parts.append(f"trace_id='{self.trace_id:032x}'")
        if include_span_id:
            first_line_parts.append(f"span_id='{self.span_id:016x}'")
        if include_start_timestamp:
            first_line_parts.append(f'start_timestamp={self.start_timestamp.isoformat()!r}')
        if include_duration:
            first_line_parts.append(f"duration='{self.duration}'")

        extra_lines: list[str] = []
        if include_children and self.children:
            first_line_parts.append('>')
            for child in self.children:
                extra_lines.append(
                    indent(
                        child.repr_xml(
                            include_children=include_children,
                            include_trace_id=include_trace_id,
                            include_span_id=include_span_id,
                            include_start_timestamp=include_start_timestamp,
                            include_duration=include_duration,
                        ),
                        '  ',
                    )
                )
            extra_lines.append('</SpanNode>')
        else:
            if self.children:
                first_line_parts.append('children=...')
            first_line_parts.append('/>')
        return '\n'.join([' '.join(first_line_parts), *extra_lines])

    def __str__(self) -> str:
        if self.children:
            return f"<SpanNode name={self.name!r} span_id='{self.span_id:016x}'>...</SpanNode>"
        else:
            return f"<SpanNode name={self.name!r} span_id='{self.span_id:016x}' />"

    def __repr__(self) -> str:
        return self.repr_xml()

```

#### duration

```python
duration: timedelta

```

Return the span's duration as a timedelta, or None if start/end not set.

#### descendants

```python
descendants: list[SpanNode]

```

Return all descendants of this node in DFS order.

#### ancestors

```python
ancestors: list[SpanNode]

```

Return all ancestors of this node.

#### add_child

```python
add_child(child: SpanNode) -> None

```

Attach a child node to this node's list of children.

Source code in `pydantic_evals/pydantic_evals/otel/span_tree.py`

```python
def add_child(self, child: SpanNode) -> None:
    """Attach a child node to this node's list of children."""
    assert child.trace_id == self.trace_id, f"traces don't match: {child.trace_id:032x} != {self.trace_id:032x}"
    assert child.parent_span_id == self.span_id, (
        f'parent span mismatch: {child.parent_span_id:016x} != {self.span_id:016x}'
    )
    self.children_by_id[child.node_key] = child
    child.parent = self

```

#### find_children

```python
find_children(
    predicate: SpanQuery | SpanPredicate,
) -> list[SpanNode]

```

Return all immediate children that satisfy the given predicate.

Source code in `pydantic_evals/pydantic_evals/otel/span_tree.py`

```python
def find_children(self, predicate: SpanQuery | SpanPredicate) -> list[SpanNode]:
    """Return all immediate children that satisfy the given predicate."""
    return list(self._filter_children(predicate))

```

#### first_child

```python
first_child(
    predicate: SpanQuery | SpanPredicate,
) -> SpanNode | None

```

Return the first immediate child that satisfies the given predicate, or None if none match.

Source code in `pydantic_evals/pydantic_evals/otel/span_tree.py`

```python
def first_child(self, predicate: SpanQuery | SpanPredicate) -> SpanNode | None:
    """Return the first immediate child that satisfies the given predicate, or None if none match."""
    return next(self._filter_children(predicate), None)

```

#### any_child

```python
any_child(predicate: SpanQuery | SpanPredicate) -> bool

```

Returns True if there is at least one child that satisfies the predicate.

Source code in `pydantic_evals/pydantic_evals/otel/span_tree.py`

```python
def any_child(self, predicate: SpanQuery | SpanPredicate) -> bool:
    """Returns True if there is at least one child that satisfies the predicate."""
    return self.first_child(predicate) is not None

```

#### find_descendants

```python
find_descendants(
    predicate: SpanQuery | SpanPredicate,
    stop_recursing_when: (
        SpanQuery | SpanPredicate | None
    ) = None,
) -> list[SpanNode]

```

Return all descendant nodes that satisfy the given predicate in DFS order.

Source code in `pydantic_evals/pydantic_evals/otel/span_tree.py`

```python
def find_descendants(
    self, predicate: SpanQuery | SpanPredicate, stop_recursing_when: SpanQuery | SpanPredicate | None = None
) -> list[SpanNode]:
    """Return all descendant nodes that satisfy the given predicate in DFS order."""
    return list(self._filter_descendants(predicate, stop_recursing_when))

```

#### first_descendant

```python
first_descendant(
    predicate: SpanQuery | SpanPredicate,
    stop_recursing_when: (
        SpanQuery | SpanPredicate | None
    ) = None,
) -> SpanNode | None

```

DFS: Return the first descendant (in DFS order) that satisfies the given predicate, or `None` if none match.

Source code in `pydantic_evals/pydantic_evals/otel/span_tree.py`

```python
def first_descendant(
    self, predicate: SpanQuery | SpanPredicate, stop_recursing_when: SpanQuery | SpanPredicate | None = None
) -> SpanNode | None:
    """DFS: Return the first descendant (in DFS order) that satisfies the given predicate, or `None` if none match."""
    return next(self._filter_descendants(predicate, stop_recursing_when), None)

```

#### any_descendant

```python
any_descendant(
    predicate: SpanQuery | SpanPredicate,
    stop_recursing_when: (
        SpanQuery | SpanPredicate | None
    ) = None,
) -> bool

```

Returns `True` if there is at least one descendant that satisfies the predicate.

Source code in `pydantic_evals/pydantic_evals/otel/span_tree.py`

```python
def any_descendant(
    self, predicate: SpanQuery | SpanPredicate, stop_recursing_when: SpanQuery | SpanPredicate | None = None
) -> bool:
    """Returns `True` if there is at least one descendant that satisfies the predicate."""
    return self.first_descendant(predicate, stop_recursing_when) is not None

```

#### find_ancestors

```python
find_ancestors(
    predicate: SpanQuery | SpanPredicate,
    stop_recursing_when: (
        SpanQuery | SpanPredicate | None
    ) = None,
) -> list[SpanNode]

```

Return all ancestors that satisfy the given predicate.

Source code in `pydantic_evals/pydantic_evals/otel/span_tree.py`

```python
def find_ancestors(
    self, predicate: SpanQuery | SpanPredicate, stop_recursing_when: SpanQuery | SpanPredicate | None = None
) -> list[SpanNode]:
    """Return all ancestors that satisfy the given predicate."""
    return list(self._filter_ancestors(predicate, stop_recursing_when))

```

#### first_ancestor

```python
first_ancestor(
    predicate: SpanQuery | SpanPredicate,
    stop_recursing_when: (
        SpanQuery | SpanPredicate | None
    ) = None,
) -> SpanNode | None

```

Return the closest ancestor that satisfies the given predicate, or `None` if none match.

Source code in `pydantic_evals/pydantic_evals/otel/span_tree.py`

```python
def first_ancestor(
    self, predicate: SpanQuery | SpanPredicate, stop_recursing_when: SpanQuery | SpanPredicate | None = None
) -> SpanNode | None:
    """Return the closest ancestor that satisfies the given predicate, or `None` if none match."""
    return next(self._filter_ancestors(predicate, stop_recursing_when), None)

```

#### any_ancestor

```python
any_ancestor(
    predicate: SpanQuery | SpanPredicate,
    stop_recursing_when: (
        SpanQuery | SpanPredicate | None
    ) = None,
) -> bool

```

Returns True if any ancestor satisfies the predicate.

Source code in `pydantic_evals/pydantic_evals/otel/span_tree.py`

```python
def any_ancestor(
    self, predicate: SpanQuery | SpanPredicate, stop_recursing_when: SpanQuery | SpanPredicate | None = None
) -> bool:
    """Returns True if any ancestor satisfies the predicate."""
    return self.first_ancestor(predicate, stop_recursing_when) is not None

```

#### matches

```python
matches(query: SpanQuery | SpanPredicate) -> bool

```

Check if the span node matches the query conditions or predicate.

Source code in `pydantic_evals/pydantic_evals/otel/span_tree.py`

```python
def matches(self, query: SpanQuery | SpanPredicate) -> bool:
    """Check if the span node matches the query conditions or predicate."""
    if callable(query):
        return query(self)

    return self._matches_query(query)

```

#### repr_xml

```python
repr_xml(
    include_children: bool = True,
    include_trace_id: bool = False,
    include_span_id: bool = False,
    include_start_timestamp: bool = False,
    include_duration: bool = False,
) -> str

```

Return an XML-like string representation of the node.

Optionally includes children, trace_id, span_id, start_timestamp, and duration.

Source code in `pydantic_evals/pydantic_evals/otel/span_tree.py`

```python
def repr_xml(
    self,
    include_children: bool = True,
    include_trace_id: bool = False,
    include_span_id: bool = False,
    include_start_timestamp: bool = False,
    include_duration: bool = False,
) -> str:
    """Return an XML-like string representation of the node.

    Optionally includes children, trace_id, span_id, start_timestamp, and duration.
    """
    first_line_parts = [f'<SpanNode name={self.name!r}']
    if include_trace_id:
        first_line_parts.append(f"trace_id='{self.trace_id:032x}'")
    if include_span_id:
        first_line_parts.append(f"span_id='{self.span_id:016x}'")
    if include_start_timestamp:
        first_line_parts.append(f'start_timestamp={self.start_timestamp.isoformat()!r}')
    if include_duration:
        first_line_parts.append(f"duration='{self.duration}'")

    extra_lines: list[str] = []
    if include_children and self.children:
        first_line_parts.append('>')
        for child in self.children:
            extra_lines.append(
                indent(
                    child.repr_xml(
                        include_children=include_children,
                        include_trace_id=include_trace_id,
                        include_span_id=include_span_id,
                        include_start_timestamp=include_start_timestamp,
                        include_duration=include_duration,
                    ),
                    '  ',
                )
            )
        extra_lines.append('</SpanNode>')
    else:
        if self.children:
            first_line_parts.append('children=...')
        first_line_parts.append('/>')
    return '\n'.join([' '.join(first_line_parts), *extra_lines])

```
