### Prefixing Tool Names

PrefixedToolset wraps a toolset and adds a prefix to each tool name to prevent tool name conflicts between different toolsets.

To easily chain different modifications, you can also call prefixed() on any toolset instead of directly constructing a `PrefixedToolset`.

combined_toolset.py

```python
from pydantic_ai import Agent, CombinedToolset
from pydantic_ai.models.test import TestModel

from function_toolset import datetime_toolset, weather_toolset

combined_toolset = CombinedToolset(
    [
        weather_toolset.prefixed('weather'),
        datetime_toolset.prefixed('datetime')
    ]
)

test_model = TestModel() # (1)!
agent = Agent(test_model, toolsets=[combined_toolset])
result = agent.run_sync('What tools are available?')
print([t.name for t in test_model.last_model_request_parameters.function_tools])
"""
[
    'weather_temperature_celsius',
    'weather_temperature_fahrenheit',
    'weather_conditions',
    'datetime_now',
]
"""

```

1. We're using TestModel here because it makes it easy to see which tools were available on each run.

_(This example is complete, it can be run "as is")_
