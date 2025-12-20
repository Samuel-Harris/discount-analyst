### StructuredDict

```python
StructuredDict(
    json_schema: JsonSchemaValue,
    name: str | None = None,
    description: str | None = None,
) -> type[JsonSchemaValue]

```

Returns a `dict[str, Any]` subclass with a JSON schema attached that will be used for structured output.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `json_schema` | `JsonSchemaValue` | A JSON schema of type object defining the structure of the dictionary content. | _required_ | | `name` | `str | None` | Optional name of the structured output. If not provided, the title field of the JSON schema will be used if it's present. | `None` | | `description` | `str | None` | Optional description of the structured output. If not provided, the description field of the JSON schema will be used if it's present. | `None` |

Example: structured_dict.py

```python
from pydantic_ai import Agent, StructuredDict

schema = {
    'type': 'object',
    'properties': {
        'name': {'type': 'string'},
        'age': {'type': 'integer'}
    },
    'required': ['name', 'age']
}

agent = Agent('openai:gpt-4o', output_type=StructuredDict(schema))
result = agent.run_sync('Create a person')
print(result.output)
#> {'name': 'John Doe', 'age': 30}

```

Source code in `pydantic_ai_slim/pydantic_ai/output.py`

````python
def StructuredDict(
    json_schema: JsonSchemaValue, name: str | None = None, description: str | None = None
) -> type[JsonSchemaValue]:
    """Returns a `dict[str, Any]` subclass with a JSON schema attached that will be used for structured output.

    Args:
        json_schema: A JSON schema of type `object` defining the structure of the dictionary content.
        name: Optional name of the structured output. If not provided, the `title` field of the JSON schema will be used if it's present.
        description: Optional description of the structured output. If not provided, the `description` field of the JSON schema will be used if it's present.

    Example:
    ```python {title="structured_dict.py"}
    from pydantic_ai import Agent, StructuredDict

    schema = {
        'type': 'object',
        'properties': {
            'name': {'type': 'string'},
            'age': {'type': 'integer'}
        },
        'required': ['name', 'age']
    }

    agent = Agent('openai:gpt-4o', output_type=StructuredDict(schema))
    result = agent.run_sync('Create a person')
    print(result.output)
    #> {'name': 'John Doe', 'age': 30}
    ```
    """
    json_schema = _utils.check_object_json_schema(json_schema)

    # Pydantic `TypeAdapter` fails when `object.__get_pydantic_json_schema__` has `$defs`, so we inline them
    # See https://github.com/pydantic/pydantic/issues/12145
    if '$defs' in json_schema:
        json_schema = InlineDefsJsonSchemaTransformer(json_schema).walk()
        if '$defs' in json_schema:
            raise exceptions.UserError(
                '`StructuredDict` does not currently support recursive `$ref`s and `$defs`. See https://github.com/pydantic/pydantic/issues/12145 for more information.'
            )

    if name:
        json_schema['title'] = name

    if description:
        json_schema['description'] = description

    class _StructuredDict(JsonSchemaValue):
        __is_model_like__ = True

        @classmethod
        def __get_pydantic_core_schema__(
            cls, source_type: Any, handler: GetCoreSchemaHandler
        ) -> core_schema.CoreSchema:
            return core_schema.dict_schema(
                keys_schema=core_schema.str_schema(),
                values_schema=core_schema.any_schema(),
            )

        @classmethod
        def __get_pydantic_json_schema__(
            cls, core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
        ) -> JsonSchemaValue:
            return json_schema

    return _StructuredDict

````
