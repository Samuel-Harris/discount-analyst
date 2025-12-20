### Dynamic Tool Definitions

PreparedToolset lets you modify the entire list of available tools ahead of each step of the agent run using a user-defined function that takes the agent run context and a list of ToolDefinitions and returns a list of modified `ToolDefinition`s.

This is the toolset-specific equivalent of the [`prepare_tools`](../tools-advanced/#prepare-tools) argument to `Agent` that prepares all tool definitions registered on an agent across toolsets.

Note that it is not possible to add or rename tools using `PreparedToolset`. Instead, you can use [`FunctionToolset.add_function()`](#function-toolset) or [`RenamedToolset`](#renaming-tools).

To easily chain different modifications, you can also call prepared() on any toolset instead of directly constructing a `PreparedToolset`.

prepared_toolset.py

```python
from dataclasses import replace

from pydantic_ai import Agent, RunContext, ToolDefinition
from pydantic_ai.models.test import TestModel

from renamed_toolset import renamed_toolset

descriptions = {
    'temperature_celsius': 'Get the temperature in degrees Celsius',
    'temperature_fahrenheit': 'Get the temperature in degrees Fahrenheit',
    'weather_conditions': 'Get the current weather conditions',
    'current_time': 'Get the current time',
}

async def add_descriptions(ctx: RunContext, tool_defs: list[ToolDefinition]) -> list[ToolDefinition] | None:
    return [
        replace(tool_def, description=description)
        if (description := descriptions.get(tool_def.name, None))
        else tool_def
        for tool_def
        in tool_defs
    ]

prepared_toolset = renamed_toolset.prepared(add_descriptions)

test_model = TestModel() # (1)!
agent = Agent(test_model, toolsets=[prepared_toolset])
result = agent.run_sync('What tools are available?')
print(test_model.last_model_request_parameters.function_tools)
"""
[
    ToolDefinition(
        name='temperature_celsius',
        parameters_json_schema={
            'additionalProperties': False,
            'properties': {'city': {'type': 'string'}},
            'required': ['city'],
            'type': 'object',
        },
        description='Get the temperature in degrees Celsius',
    ),
    ToolDefinition(
        name='temperature_fahrenheit',
        parameters_json_schema={
            'additionalProperties': False,
            'properties': {'city': {'type': 'string'}},
            'required': ['city'],
            'type': 'object',
        },
        description='Get the temperature in degrees Fahrenheit',
    ),
    ToolDefinition(
        name='weather_conditions',
        parameters_json_schema={
            'additionalProperties': False,
            'properties': {'city': {'type': 'string'}},
            'required': ['city'],
            'type': 'object',
        },
        description='Get the current weather conditions',
    ),
    ToolDefinition(
        name='current_time',
        parameters_json_schema={
            'additionalProperties': False,
            'properties': {},
            'type': 'object',
        },
        description='Get the current time',
    ),
]
"""

```

1. We're using TestModel here because it makes it easy to see which tools were available on each run.
