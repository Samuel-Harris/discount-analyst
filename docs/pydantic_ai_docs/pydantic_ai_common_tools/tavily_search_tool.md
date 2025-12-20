### tavily_search_tool

```python
tavily_search_tool(api_key: str)

```

Creates a Tavily search tool.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `api_key` | `str` | The Tavily API key. You can get one by signing up at https://app.tavily.com/home. | _required_ |

Source code in `pydantic_ai_slim/pydantic_ai/common_tools/tavily.py`

```python
def tavily_search_tool(api_key: str):
    """Creates a Tavily search tool.

    Args:
        api_key: The Tavily API key.

            You can get one by signing up at [https://app.tavily.com/home](https://app.tavily.com/home).
    """
    return Tool[Any](
        TavilySearchTool(client=AsyncTavilyClient(api_key)).__call__,
        name='tavily_search',
        description='Searches Tavily for the given query and returns the results.',
    )

```
