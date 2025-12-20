### Renaming Tools

RenamedToolset wraps a toolset and lets you rename tools using a dictionary mapping new names to original names. This is useful when the names provided by a toolset are ambiguous or would conflict with tools defined by other toolsets, but [prefixing them](#prefixing-tool-names) creates a name that is unnecessarily long or could be confusing to the model.

To easily chain different modifications, you can also call renamed() on any toolset instead of directly constructing a `RenamedToolset`.

renamed_toolset.py

```python
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel

from combined_toolset import combined_toolset

renamed_toolset = combined_toolset.renamed(
    {
        'current_time': 'datetime_now',
        'temperature_celsius': 'weather_temperature_celsius',
        'temperature_fahrenheit': 'weather_temperature_fahrenheit'
    }
)

test_model = TestModel() # (1)!
agent = Agent(test_model, toolsets=[renamed_toolset])
result = agent.run_sync('What tools are available?')
print([t.name for t in test_model.last_model_request_parameters.function_tools])
"""
['temperature_celsius', 'temperature_fahrenheit', 'weather_conditions', 'current_time']
"""

```

1. We're using TestModel here because it makes it easy to see which tools were available on each run.

_(This example is complete, it can be run "as is")_
