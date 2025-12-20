### duckduckgo_search_tool

```python
duckduckgo_search_tool(
    duckduckgo_client: DDGS | None = None,
    max_results: int | None = None,
)

```

Creates a DuckDuckGo search tool.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `duckduckgo_client` | `DDGS | None` | The DuckDuckGo search client. | `None` | | `max_results` | `int | None` | The maximum number of results. If None, returns results only from the first response. | `None` |

Source code in `pydantic_ai_slim/pydantic_ai/common_tools/duckduckgo.py`

```python
def duckduckgo_search_tool(duckduckgo_client: DDGS | None = None, max_results: int | None = None):
    """Creates a DuckDuckGo search tool.

    Args:
        duckduckgo_client: The DuckDuckGo search client.
        max_results: The maximum number of results. If None, returns results only from the first response.
    """
    return Tool[Any](
        DuckDuckGoSearchTool(client=duckduckgo_client or DDGS(), max_results=max_results).__call__,
        name='duckduckgo_search',
        description='Searches DuckDuckGo for the given query and returns the results.',
    )

```
