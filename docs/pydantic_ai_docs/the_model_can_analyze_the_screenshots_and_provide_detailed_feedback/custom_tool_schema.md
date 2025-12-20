## Custom Tool Schema

If you have a function that lacks appropriate documentation (i.e. poorly named, no type information, poor docstring, use of \*args or \*\*kwargs and suchlike) then you can still turn it into a tool that can be effectively used by the agent with the Tool.from_schema function. With this you provide the name, description, JSON schema, and whether the function takes a `RunContext` for the function directly:

```python
from pydantic_ai import Agent, Tool
from pydantic_ai.models.test import TestModel


def foobar(**kwargs) -> str:
    return kwargs['a'] + kwargs['b']

tool = Tool.from_schema(
    function=foobar,
    name='sum',
    description='Sum two numbers.',
    json_schema={
        'additionalProperties': False,
        'properties': {
            'a': {'description': 'the first number', 'type': 'integer'},
            'b': {'description': 'the second number', 'type': 'integer'},
        },
        'required': ['a', 'b'],
        'type': 'object',
    },
    takes_ctx=False,
)

test_model = TestModel()
agent = Agent(test_model, tools=[tool])

result = agent.run_sync('testing...')
print(result.output)
#> {"sum":0}

```

Please note that validation of the tool arguments will not be performed, and this will pass all arguments as keyword arguments.
