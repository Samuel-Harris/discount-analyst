### generate_code

```python
generate_code(
    graph: Graph[Any, Any, Any],
    /,
    *,
    start_node: (
        Sequence[NodeIdent] | NodeIdent | None
    ) = None,
    highlighted_nodes: (
        Sequence[NodeIdent] | NodeIdent | None
    ) = None,
    highlight_css: str = DEFAULT_HIGHLIGHT_CSS,
    title: str | None = None,
    edge_labels: bool = True,
    notes: bool = True,
    direction: StateDiagramDirection | None,
) -> str

```

Generate [Mermaid state diagram](https://mermaid.js.org/syntax/stateDiagram.html) code for a graph.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `graph` | `Graph[Any, Any, Any]` | The graph to generate the image for. | _required_ | | `start_node` | `Sequence[NodeIdent] | NodeIdent | None` | Identifiers of nodes that start the graph. | `None` | | `highlighted_nodes` | `Sequence[NodeIdent] | NodeIdent | None` | Identifiers of nodes to highlight. | `None` | | `highlight_css` | `str` | CSS to use for highlighting nodes. | `DEFAULT_HIGHLIGHT_CSS` | | `title` | `str | None` | The title of the diagram. | `None` | | `edge_labels` | `bool` | Whether to include edge labels in the diagram. | `True` | | `notes` | `bool` | Whether to include notes in the diagram. | `True` | | `direction` | `StateDiagramDirection | None` | The direction of flow. | _required_ |

Returns:

| Type | Description | | --- | --- | | `str` | The Mermaid code for the graph. |

Source code in `pydantic_graph/pydantic_graph/mermaid.py`

```python
def generate_code(  # noqa: C901
    graph: Graph[Any, Any, Any],
    /,
    *,
    start_node: Sequence[NodeIdent] | NodeIdent | None = None,
    highlighted_nodes: Sequence[NodeIdent] | NodeIdent | None = None,
    highlight_css: str = DEFAULT_HIGHLIGHT_CSS,
    title: str | None = None,
    edge_labels: bool = True,
    notes: bool = True,
    direction: StateDiagramDirection | None,
) -> str:
    """Generate [Mermaid state diagram](https://mermaid.js.org/syntax/stateDiagram.html) code for a graph.

    Args:
        graph: The graph to generate the image for.
        start_node: Identifiers of nodes that start the graph.
        highlighted_nodes: Identifiers of nodes to highlight.
        highlight_css: CSS to use for highlighting nodes.
        title: The title of the diagram.
        edge_labels: Whether to include edge labels in the diagram.
        notes: Whether to include notes in the diagram.
        direction: The direction of flow.


    Returns:
        The Mermaid code for the graph.
    """
    start_node_ids = set(_node_ids(start_node or ()))
    for node_id in start_node_ids:
        if node_id not in graph.node_defs:
            raise LookupError(f'Start node "{node_id}" is not in the graph.')

    lines: list[str] = []
    if title:
        lines = ['---', f'title: {title}', '---']
    lines.append('stateDiagram-v2')
    if direction is not None:
        lines.append(f'  direction {direction}')
    for node_id, node_def in graph.node_defs.items():
        # we use round brackets (rounded box) for nodes other than the start and end
        if node_id in start_node_ids:
            lines.append(f'  [*] --> {node_id}')
        if node_def.returns_base_node:
            for next_node_id in graph.node_defs:
                lines.append(f'  {node_id} --> {next_node_id}')
        else:
            for next_node_id, edge in node_def.next_node_edges.items():
                line = f'  {node_id} --> {next_node_id}'
                if edge_labels and edge.label:
                    line += f': {edge.label}'
                lines.append(line)
        if end_edge := node_def.end_edge:
            line = f'  {node_id} --> [*]'
            if edge_labels and end_edge.label:
                line += f': {end_edge.label}'
            lines.append(line)

        if notes and node_def.note:
            lines.append(f'  note right of {node_id}')
            # mermaid doesn't like multiple paragraphs in a note, and shows if so
            clean_docs = re.sub('\n{2,}', '\n', node_def.note)
            lines.append(indent(clean_docs, '    '))
            lines.append('  end note')

    if highlighted_nodes:
        lines.append('')
        lines.append(f'classDef highlighted {highlight_css}')
        for node_id in _node_ids(highlighted_nodes):
            if node_id not in graph.node_defs:
                raise LookupError(f'Highlighted node "{node_id}" is not in the graph.')
            lines.append(f'class {node_id} highlighted')

    return '\n'.join(lines)

```
