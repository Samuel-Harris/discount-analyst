### tool_from_langchain

```python
tool_from_langchain(langchain_tool: LangChainTool) -> Tool

```

Creates a Pydantic AI tool proxy from a LangChain tool.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `langchain_tool` | `LangChainTool` | The LangChain tool to wrap. | _required_ |

Returns:

| Type | Description | | --- | --- | | `Tool` | A Pydantic AI tool that corresponds to the LangChain tool. |

Source code in `pydantic_ai_slim/pydantic_ai/ext/langchain.py`

```python
def tool_from_langchain(langchain_tool: LangChainTool) -> Tool:
    """Creates a Pydantic AI tool proxy from a LangChain tool.

    Args:
        langchain_tool: The LangChain tool to wrap.

    Returns:
        A Pydantic AI tool that corresponds to the LangChain tool.
    """
    function_name = langchain_tool.name
    function_description = langchain_tool.description
    inputs = langchain_tool.args.copy()
    required = sorted({name for name, detail in inputs.items() if 'default' not in detail})
    schema: JsonSchemaValue = langchain_tool.get_input_jsonschema()
    if 'additionalProperties' not in schema:
        schema['additionalProperties'] = False
    if required:
        schema['required'] = required

    defaults = {name: detail['default'] for name, detail in inputs.items() if 'default' in detail}

    # restructures the arguments to match langchain tool run
    def proxy(*args: Any, **kwargs: Any) -> str:
        assert not args, 'This should always be called with kwargs'
        kwargs = defaults | kwargs
        return langchain_tool.run(kwargs)

    return Tool.from_schema(
        function=proxy,
        name=function_name,
        description=function_description,
        json_schema=schema,
    )

```
