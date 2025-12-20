### Combining Toolsets

CombinedToolset takes a list of toolsets and lets them be used as one.

combined_toolset.py

```python
from pydantic_ai import Agent, CombinedToolset
from pydantic_ai.models.test import TestModel

from function_toolset import datetime_toolset, weather_toolset

combined_toolset = CombinedToolset([weather_toolset, datetime_toolset])

test_model = TestModel() # (1)!
agent = Agent(test_model, toolsets=[combined_toolset])
result = agent.run_sync('What tools are available?')
print([t.name for t in test_model.last_model_request_parameters.function_tools])
#> ['temperature_celsius', 'temperature_fahrenheit', 'conditions', 'now']

```

1. We're using TestModel here because it makes it easy to see which tools were available on each run.

_(This example is complete, it can be run "as is")_
