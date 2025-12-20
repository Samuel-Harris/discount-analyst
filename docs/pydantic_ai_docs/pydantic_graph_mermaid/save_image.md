### save_image

```python
save_image(
    path: Path | str,
    graph: Graph[Any, Any, Any],
    /,
    **kwargs: Unpack[MermaidConfig],
) -> None

```

Generate an image of a Mermaid diagram using [mermaid.ink](https://mermaid.ink) and save it to a local file.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `path` | `Path | str` | The path to save the image to. | _required_ | | `graph` | `Graph[Any, Any, Any]` | The graph to generate the image for. | _required_ | | `**kwargs` | `Unpack[MermaidConfig]` | Additional parameters to configure mermaid chart generation. | `{}` |

Source code in `pydantic_graph/pydantic_graph/mermaid.py`

```python
def save_image(
    path: Path | str,
    graph: Graph[Any, Any, Any],
    /,
    **kwargs: Unpack[MermaidConfig],
) -> None:
    """Generate an image of a Mermaid diagram using [mermaid.ink](https://mermaid.ink) and save it to a local file.

    Args:
        path: The path to save the image to.
        graph: The graph to generate the image for.
        **kwargs: Additional parameters to configure mermaid chart generation.
    """
    if isinstance(path, str):
        path = Path(path)

    if 'image_type' not in kwargs:
        ext = path.suffix.lower()[1:]
        # no need to check for .jpeg/.jpg, as it is the default
        if ext in ('png', 'webp', 'svg', 'pdf'):
            kwargs['image_type'] = ext

    image_data = request_image(graph, **kwargs)
    path.write_bytes(image_data)

```
