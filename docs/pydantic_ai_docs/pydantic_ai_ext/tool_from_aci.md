### tool_from_aci

```python
tool_from_aci(
    aci_function: str, linked_account_owner_id: str
) -> Tool

```

Creates a Pydantic AI tool proxy from an ACI.dev function.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `aci_function` | `str` | The ACI.dev function to wrap. | _required_ | | `linked_account_owner_id` | `str` | The ACI user ID to execute the function on behalf of. | _required_ |

Returns:

| Type | Description | | --- | --- | | `Tool` | A Pydantic AI tool that corresponds to the ACI.dev tool. |

Source code in `pydantic_ai_slim/pydantic_ai/ext/aci.py`

```python
def tool_from_aci(aci_function: str, linked_account_owner_id: str) -> Tool:
    """Creates a Pydantic AI tool proxy from an ACI.dev function.

    Args:
        aci_function: The ACI.dev function to wrap.
        linked_account_owner_id: The ACI user ID to execute the function on behalf of.

    Returns:
        A Pydantic AI tool that corresponds to the ACI.dev tool.
    """
    aci = ACI()
    function_definition = aci.functions.get_definition(aci_function)
    function_name = function_definition['function']['name']
    function_description = function_definition['function']['description']
    inputs = function_definition['function']['parameters']

    json_schema = {
        'additionalProperties': inputs.get('additionalProperties', False),
        'properties': inputs.get('properties', {}),
        'required': inputs.get('required', []),
        # Default to 'object' if not specified
        'type': inputs.get('type', 'object'),
    }

    # Clean the schema
    json_schema = _clean_schema(json_schema)

    def implementation(*args: Any, **kwargs: Any) -> str:
        if args:
            raise TypeError('Positional arguments are not allowed')
        return aci.handle_function_call(
            function_name,
            kwargs,
            linked_account_owner_id=linked_account_owner_id,
            allowed_apps_only=True,
        )

    return Tool.from_schema(
        function=implementation,
        name=function_name,
        description=function_description,
        json_schema=json_schema,
    )

```
