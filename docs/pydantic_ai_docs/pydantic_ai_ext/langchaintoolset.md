### LangChainToolset

Bases: `FunctionToolset`

A toolset that wraps LangChain tools.

Source code in `pydantic_ai_slim/pydantic_ai/ext/langchain.py`

```python
class LangChainToolset(FunctionToolset):
    """A toolset that wraps LangChain tools."""

    def __init__(self, tools: list[LangChainTool], *, id: str | None = None):
        super().__init__([tool_from_langchain(tool) for tool in tools], id=id)

```
