### request_image

```python
request_image(
    graph: Graph[Any, Any, Any],
    /,
    **kwargs: Unpack[MermaidConfig],
) -> bytes

```

Generate an image of a Mermaid diagram using [mermaid.ink](https://mermaid.ink).

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `graph` | `Graph[Any, Any, Any]` | The graph to generate the image for. | _required_ | | `**kwargs` | `Unpack[MermaidConfig]` | Additional parameters to configure mermaid chart generation. | `{}` |

Returns:

| Type | Description | | --- | --- | | `bytes` | The image data. |

Source code in `pydantic_graph/pydantic_graph/mermaid.py`

```python
def request_image(
    graph: Graph[Any, Any, Any],
    /,
    **kwargs: Unpack[MermaidConfig],
) -> bytes:
    """Generate an image of a Mermaid diagram using [mermaid.ink](https://mermaid.ink).

    Args:
        graph: The graph to generate the image for.
        **kwargs: Additional parameters to configure mermaid chart generation.

    Returns:
        The image data.
    """
    code = generate_code(
        graph,
        start_node=kwargs.get('start_node'),
        highlighted_nodes=kwargs.get('highlighted_nodes'),
        highlight_css=kwargs.get('highlight_css', DEFAULT_HIGHLIGHT_CSS),
        title=kwargs.get('title'),
        edge_labels=kwargs.get('edge_labels', True),
        notes=kwargs.get('notes', True),
        direction=kwargs.get('direction'),
    )
    code_base64 = base64.b64encode(code.encode()).decode()

    params: dict[str, str | float] = {}
    if kwargs.get('image_type') == 'pdf':
        url = f'https://mermaid.ink/pdf/{code_base64}'
        if kwargs.get('pdf_fit'):
            params['fit'] = ''
        if kwargs.get('pdf_landscape'):
            params['landscape'] = ''
        if pdf_paper := kwargs.get('pdf_paper'):
            params['paper'] = pdf_paper
    elif kwargs.get('image_type') == 'svg':
        url = f'https://mermaid.ink/svg/{code_base64}'
    else:
        url = f'https://mermaid.ink/img/{code_base64}'

        if image_type := kwargs.get('image_type'):
            params['type'] = image_type

    if background_color := kwargs.get('background_color'):
        params['bgColor'] = background_color
    if theme := kwargs.get('theme'):
        params['theme'] = theme
    if width := kwargs.get('width'):
        params['width'] = width
    if height := kwargs.get('height'):
        params['height'] = height
    if scale := kwargs.get('scale'):
        params['scale'] = scale

    httpx_client = kwargs.get('httpx_client') or httpx.Client()
    response = httpx_client.get(url, params=params)
    if not response.is_success:
        raise httpx.HTTPStatusError(
            f'{response.status_code} error generating image:\n{response.text}',
            request=response.request,
            response=response,
        )
    return response.content

```
