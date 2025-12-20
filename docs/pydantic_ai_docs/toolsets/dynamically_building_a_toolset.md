## Dynamically Building a Toolset

Toolsets can be built dynamically ahead of each agent run or run step using a function that takes the agent run context and returns a toolset or `None`. This is useful when a toolset (like an MCP server) depends on information specific to an agent run, like its [dependencies](../dependencies/).

To register a dynamic toolset, you can pass a function that takes RunContext to the `toolsets` argument of the `Agent` constructor, or you can wrap a compliant function in the @agent.toolset decorator.

By default, the function will be called again ahead of each agent run step. If you are using the decorator, you can optionally provide a `per_run_step=False` argument to indicate that the toolset only needs to be built once for the entire run.

dynamic_toolset.py

```python
from dataclasses import dataclass
from typing import Literal

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.test import TestModel

from function_toolset import datetime_toolset, weather_toolset


@dataclass
class ToggleableDeps:
    active: Literal['weather', 'datetime']

    def toggle(self):
        if self.active == 'weather':
            self.active = 'datetime'
        else:
            self.active = 'weather'

test_model = TestModel()  # (1)!
agent = Agent(
    test_model,
    deps_type=ToggleableDeps  # (2)!
)

@agent.toolset
def toggleable_toolset(ctx: RunContext[ToggleableDeps]):
    if ctx.deps.active == 'weather':
        return weather_toolset
    else:
        return datetime_toolset

@agent.tool
def toggle(ctx: RunContext[ToggleableDeps]):
    ctx.deps.toggle()

deps = ToggleableDeps('weather')

result = agent.run_sync('Toggle the toolset', deps=deps)
print([t.name for t in test_model.last_model_request_parameters.function_tools])  # (3)!
#> ['toggle', 'now']

result = agent.run_sync('Toggle the toolset', deps=deps)
print([t.name for t in test_model.last_model_request_parameters.function_tools])
#> ['toggle', 'temperature_celsius', 'temperature_fahrenheit', 'conditions']

```

1. We're using TestModel here because it makes it easy to see which tools were available on each run.
1. We're using the agent's dependencies to give the `toggle` tool access to the `active` via the `RunContext` argument.
1. This shows the available tools _after_ the `toggle` tool was executed, as the "last model request" was the one that returned the `toggle` tool result to the model.

_(This example is complete, it can be run "as is")_
