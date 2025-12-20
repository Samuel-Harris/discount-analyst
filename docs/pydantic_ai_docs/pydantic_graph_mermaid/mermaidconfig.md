### MermaidConfig

Bases: `TypedDict`

Parameters to configure mermaid chart generation.

Source code in `pydantic_graph/pydantic_graph/mermaid.py`

```python
class MermaidConfig(TypedDict, total=False):
    """Parameters to configure mermaid chart generation."""

    start_node: Sequence[NodeIdent] | NodeIdent
    """Identifiers of nodes that start the graph."""
    highlighted_nodes: Sequence[NodeIdent] | NodeIdent
    """Identifiers of nodes to highlight."""
    highlight_css: str
    """CSS to use for highlighting nodes."""
    title: str | None
    """The title of the diagram."""
    edge_labels: bool
    """Whether to include edge labels in the diagram."""
    notes: bool
    """Whether to include notes on nodes in the diagram, defaults to true."""
    image_type: Literal['jpeg', 'png', 'webp', 'svg', 'pdf']
    """The image type to generate. If unspecified, the default behavior is `'jpeg'`."""
    pdf_fit: bool
    """When using image_type='pdf', whether to fit the diagram to the PDF page."""
    pdf_landscape: bool
    """When using image_type='pdf', whether to use landscape orientation for the PDF.

    This has no effect if using `pdf_fit`.
    """
    pdf_paper: Literal['letter', 'legal', 'tabloid', 'ledger', 'a0', 'a1', 'a2', 'a3', 'a4', 'a5', 'a6']
    """When using image_type='pdf', the paper size of the PDF."""
    background_color: str
    """The background color of the diagram.

    If None, the default transparent background is used. The color value is interpreted as a hexadecimal color
    code by default (and should not have a leading '#'), but you can also use named colors by prefixing the
    value with `'!'`. For example, valid choices include `background_color='!white'` or `background_color='FF0000'`.
    """
    theme: Literal['default', 'neutral', 'dark', 'forest']
    """The theme of the diagram. Defaults to 'default'."""
    width: int
    """The width of the diagram."""
    height: int
    """The height of the diagram."""
    scale: Annotated[float, Ge(1), Le(3)]
    """The scale of the diagram.

    The scale must be a number between 1 and 3, and you can only set a scale if one or both of width and height are set.
    """
    httpx_client: httpx.Client
    """An HTTPX client to use for requests, mostly for testing purposes."""
    direction: StateDiagramDirection
    """The direction of the state diagram."""

```

#### start_node

```python
start_node: Sequence[NodeIdent] | NodeIdent

```

Identifiers of nodes that start the graph.

#### highlighted_nodes

```python
highlighted_nodes: Sequence[NodeIdent] | NodeIdent

```

Identifiers of nodes to highlight.

#### highlight_css

```python
highlight_css: str

```

CSS to use for highlighting nodes.

#### title

```python
title: str | None

```

The title of the diagram.

#### edge_labels

```python
edge_labels: bool

```

Whether to include edge labels in the diagram.

#### notes

```python
notes: bool

```

Whether to include notes on nodes in the diagram, defaults to true.

#### image_type

```python
image_type: Literal['jpeg', 'png', 'webp', 'svg', 'pdf']

```

The image type to generate. If unspecified, the default behavior is `'jpeg'`.

#### pdf_fit

```python
pdf_fit: bool

```

When using image_type='pdf', whether to fit the diagram to the PDF page.

#### pdf_landscape

```python
pdf_landscape: bool

```

When using image_type='pdf', whether to use landscape orientation for the PDF.

This has no effect if using `pdf_fit`.

#### pdf_paper

```python
pdf_paper: Literal[
    "letter",
    "legal",
    "tabloid",
    "ledger",
    "a0",
    "a1",
    "a2",
    "a3",
    "a4",
    "a5",
    "a6",
]

```

When using image_type='pdf', the paper size of the PDF.

#### background_color

```python
background_color: str

```

The background color of the diagram.

If None, the default transparent background is used. The color value is interpreted as a hexadecimal color code by default (and should not have a leading '#'), but you can also use named colors by prefixing the value with `'!'`. For example, valid choices include `background_color='!white'` or `background_color='FF0000'`.

#### theme

```python
theme: Literal['default', 'neutral', 'dark', 'forest']

```

The theme of the diagram. Defaults to 'default'.

#### width

```python
width: int

```

The width of the diagram.

#### height

```python
height: int

```

The height of the diagram.

#### scale

```python
scale: Annotated[float, Ge(1), Le(3)]

```

The scale of the diagram.

The scale must be a number between 1 and 3, and you can only set a scale if one or both of width and height are set.

#### httpx_client

```python
httpx_client: Client

```

An HTTPX client to use for requests, mostly for testing purposes.

#### direction

```python
direction: StateDiagramDirection

```

The direction of the state diagram.
