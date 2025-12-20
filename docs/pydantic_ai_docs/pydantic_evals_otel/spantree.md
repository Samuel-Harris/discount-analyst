### SpanTree

A container that builds a hierarchy of SpanNode objects from a list of finished spans.

You can then search or iterate the tree to make your assertions (using DFS for traversal).

Source code in `pydantic_evals/pydantic_evals/otel/span_tree.py`

```python
@dataclass(repr=False, kw_only=True)
class SpanTree:
    """A container that builds a hierarchy of SpanNode objects from a list of finished spans.

    You can then search or iterate the tree to make your assertions (using DFS for traversal).
    """

    roots: list[SpanNode] = field(default_factory=list)
    nodes_by_id: dict[str, SpanNode] = field(default_factory=dict)

    # -------------------------------------------------------------------------
    # Construction
    # -------------------------------------------------------------------------
    def __post_init__(self):
        self._rebuild_tree()

    def add_spans(self, spans: list[SpanNode]) -> None:
        """Add a list of spans to the tree, rebuilding the tree structure."""
        for span in spans:
            self.nodes_by_id[span.node_key] = span
        self._rebuild_tree()

    def add_readable_spans(self, readable_spans: list[ReadableSpan]):
        self.add_spans([SpanNode.from_readable_span(span) for span in readable_spans])

    def _rebuild_tree(self):
        # Ensure spans are ordered by start_timestamp so that roots and children end up in the right order
        nodes = list(self.nodes_by_id.values())
        nodes.sort(key=lambda node: node.start_timestamp or datetime.min)
        self.nodes_by_id = {node.node_key: node for node in nodes}

        # Build the parent/child relationships
        for node in self.nodes_by_id.values():
            parent_node_key = node.parent_node_key
            if parent_node_key is not None:
                parent_node = self.nodes_by_id.get(parent_node_key)
                if parent_node is not None:
                    parent_node.add_child(node)

        # Determine the roots
        # A node is a "root" if its parent is None or if its parent's span_id is not in the current set of spans.
        self.roots = []
        for node in self.nodes_by_id.values():
            parent_node_key = node.parent_node_key
            if parent_node_key is None or parent_node_key not in self.nodes_by_id:
                self.roots.append(node)

    # -------------------------------------------------------------------------
    # Node filtering and iteration
    # -------------------------------------------------------------------------
    def find(self, predicate: SpanQuery | SpanPredicate) -> list[SpanNode]:
        """Find all nodes in the entire tree that match the predicate, scanning from each root in DFS order."""
        return list(self._filter(predicate))

    def first(self, predicate: SpanQuery | SpanPredicate) -> SpanNode | None:
        """Find the first node that matches a predicate, scanning from each root in DFS order. Returns `None` if not found."""
        return next(self._filter(predicate), None)

    def any(self, predicate: SpanQuery | SpanPredicate) -> bool:
        """Returns True if any node in the tree matches the predicate."""
        return self.first(predicate) is not None

    def _filter(self, predicate: SpanQuery | SpanPredicate) -> Iterator[SpanNode]:
        for node in self:
            if node.matches(predicate):
                yield node

    def __iter__(self) -> Iterator[SpanNode]:
        """Return an iterator over all nodes in the tree."""
        return iter(self.nodes_by_id.values())

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
        """Return an XML-like string representation of the tree, optionally including children, trace_id, span_id, duration, and timestamps."""
        if not self.roots:
            return '<SpanTree />'
        repr_parts = [
            '<SpanTree>',
            *[
                indent(
                    root.repr_xml(
                        include_children=include_children,
                        include_trace_id=include_trace_id,
                        include_span_id=include_span_id,
                        include_start_timestamp=include_start_timestamp,
                        include_duration=include_duration,
                    ),
                    '  ',
                )
                for root in self.roots
            ],
            '</SpanTree>',
        ]
        return '\n'.join(repr_parts)

    def __str__(self):
        return f'<SpanTree num_roots={len(self.roots)} total_spans={len(self.nodes_by_id)} />'

    def __repr__(self):
        return self.repr_xml()

```

#### add_spans

```python
add_spans(spans: list[SpanNode]) -> None

```

Add a list of spans to the tree, rebuilding the tree structure.

Source code in `pydantic_evals/pydantic_evals/otel/span_tree.py`

```python
def add_spans(self, spans: list[SpanNode]) -> None:
    """Add a list of spans to the tree, rebuilding the tree structure."""
    for span in spans:
        self.nodes_by_id[span.node_key] = span
    self._rebuild_tree()

```

#### find

```python
find(
    predicate: SpanQuery | SpanPredicate,
) -> list[SpanNode]

```

Find all nodes in the entire tree that match the predicate, scanning from each root in DFS order.

Source code in `pydantic_evals/pydantic_evals/otel/span_tree.py`

```python
def find(self, predicate: SpanQuery | SpanPredicate) -> list[SpanNode]:
    """Find all nodes in the entire tree that match the predicate, scanning from each root in DFS order."""
    return list(self._filter(predicate))

```

#### first

```python
first(
    predicate: SpanQuery | SpanPredicate,
) -> SpanNode | None

```

Find the first node that matches a predicate, scanning from each root in DFS order. Returns `None` if not found.

Source code in `pydantic_evals/pydantic_evals/otel/span_tree.py`

```python
def first(self, predicate: SpanQuery | SpanPredicate) -> SpanNode | None:
    """Find the first node that matches a predicate, scanning from each root in DFS order. Returns `None` if not found."""
    return next(self._filter(predicate), None)

```

#### any

```python
any(predicate: SpanQuery | SpanPredicate) -> bool

```

Returns True if any node in the tree matches the predicate.

Source code in `pydantic_evals/pydantic_evals/otel/span_tree.py`

```python
def any(self, predicate: SpanQuery | SpanPredicate) -> bool:
    """Returns True if any node in the tree matches the predicate."""
    return self.first(predicate) is not None

```

#### **iter**

```python
__iter__() -> Iterator[SpanNode]

```

Return an iterator over all nodes in the tree.

Source code in `pydantic_evals/pydantic_evals/otel/span_tree.py`

```python
def __iter__(self) -> Iterator[SpanNode]:
    """Return an iterator over all nodes in the tree."""
    return iter(self.nodes_by_id.values())

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

Return an XML-like string representation of the tree, optionally including children, trace_id, span_id, duration, and timestamps.

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
    """Return an XML-like string representation of the tree, optionally including children, trace_id, span_id, duration, and timestamps."""
    if not self.roots:
        return '<SpanTree />'
    repr_parts = [
        '<SpanTree>',
        *[
            indent(
                root.repr_xml(
                    include_children=include_children,
                    include_trace_id=include_trace_id,
                    include_span_id=include_span_id,
                    include_start_timestamp=include_start_timestamp,
                    include_duration=include_duration,
                ),
                '  ',
            )
            for root in self.roots
        ],
        '</SpanTree>',
    ]
    return '\n'.join(repr_parts)

```
