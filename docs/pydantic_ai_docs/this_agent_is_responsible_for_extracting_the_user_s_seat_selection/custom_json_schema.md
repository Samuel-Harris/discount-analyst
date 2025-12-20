### Custom JSON schema

If it's not feasible to define your desired structured output object using a Pydantic `BaseModel`, dataclass, or `TypedDict`, for example when you get a JSON schema from an external source or generate it dynamically, you can use the StructuredDict() helper function to generate a `dict[str, Any]` subclass with a JSON schema attached that Pydantic AI will pass to the model.

Note that Pydantic AI will not perform any validation of the received JSON object and it's up to the model to correctly interpret the schema and any constraints expressed in it, like required fields or integer value ranges.

The output type will be a `dict[str, Any]` and it's up to your code to defensively read from it in case the model made a mistake. You can use an [output validator](#output-validator-functions) to reflect validation errors back to the model and get it to try again.

Along with the JSON schema, you can optionally pass `name` and `description` arguments to provide additional context to the model:

[Learn about Gateway](../gateway)

```python
from pydantic_ai import Agent, StructuredDict

HumanDict = StructuredDict(
    {
        'type': 'object',
        'properties': {
            'name': {'type': 'string'},
            'age': {'type': 'integer'}
        },
        'required': ['name', 'age']
    },
    name='Human',
    description='A human with a name and age',
)

agent = Agent('gateway/openai:gpt-5', output_type=HumanDict)
result = agent.run_sync('Create a person')
#> {'name': 'John Doe', 'age': 30}

```

```python
from pydantic_ai import Agent, StructuredDict

HumanDict = StructuredDict(
    {
        'type': 'object',
        'properties': {
            'name': {'type': 'string'},
            'age': {'type': 'integer'}
        },
        'required': ['name', 'age']
    },
    name='Human',
    description='A human with a name and age',
)

agent = Agent('openai:gpt-5', output_type=HumanDict)
result = agent.run_sync('Create a person')
#> {'name': 'John Doe', 'age': 30}

```
