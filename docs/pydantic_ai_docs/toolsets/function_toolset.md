## Function Toolset

As the name suggests, a FunctionToolset makes locally defined functions available as tools.

Functions can be added as tools in three different ways:

- via the @toolset.tool decorator
- via the tools keyword argument to the constructor which can take either plain functions, or instances of Tool
- via the toolset.add_function() and toolset.add_tool() methods which can take a plain function or an instance of Tool respectively

Functions registered in any of these ways can define an initial `ctx: RunContext` argument in order to receive the agent run context. The `add_function()` and `add_tool()` methods can also be used from a tool function to dynamically register new tools during a run to be available in future run steps.

function_toolset.py

```python
from datetime import datetime

from pydantic_ai import Agent, FunctionToolset, RunContext
from pydantic_ai.models.test import TestModel


def temperature_celsius(city: str) -> float:
    return 21.0


def temperature_fahrenheit(city: str) -> float:
    return 69.8


weather_toolset = FunctionToolset(tools=[temperature_celsius, temperature_fahrenheit])


@weather_toolset.tool
def conditions(ctx: RunContext, city: str) -> str:
    if ctx.run_step % 2 == 0:
        return "It's sunny"
    else:
        return "It's raining"


datetime_toolset = FunctionToolset()
datetime_toolset.add_function(lambda: datetime.now(), name='now')

test_model = TestModel()  # (1)!
agent = Agent(test_model)

result = agent.run_sync('What tools are available?', toolsets=[weather_toolset])
print([t.name for t in test_model.last_model_request_parameters.function_tools])
#> ['temperature_celsius', 'temperature_fahrenheit', 'conditions']

result = agent.run_sync('What tools are available?', toolsets=[datetime_toolset])
print([t.name for t in test_model.last_model_request_parameters.function_tools])
#> ['now']

```

1. We're using TestModel here because it makes it easy to see which tools were available on each run.

_(This example is complete, it can be run "as is")_
