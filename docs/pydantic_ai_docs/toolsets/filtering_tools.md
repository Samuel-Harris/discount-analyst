### Filtering Tools

FilteredToolset wraps a toolset and filters available tools ahead of each step of the run based on a user-defined function that is passed the agent run context and each tool's ToolDefinition and returns a boolean to indicate whether or not a given tool should be available.

To easily chain different modifications, you can also call filtered() on any toolset instead of directly constructing a `FilteredToolset`.

filtered_toolset.py

```python
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel

from combined_toolset import combined_toolset

filtered_toolset = combined_toolset.filtered(lambda ctx, tool_def: 'fahrenheit' not in tool_def.name)

test_model = TestModel() # (1)!
agent = Agent(test_model, toolsets=[filtered_toolset])
result = agent.run_sync('What tools are available?')
print([t.name for t in test_model.last_model_request_parameters.function_tools])
#> ['weather_temperature_celsius', 'weather_conditions', 'datetime_now']

```

1. We're using TestModel here because it makes it easy to see which tools were available on each run.

_(This example is complete, it can be run "as is")_
