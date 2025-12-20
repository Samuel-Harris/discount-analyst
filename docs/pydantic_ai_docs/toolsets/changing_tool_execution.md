### Changing Tool Execution

WrapperToolset wraps another toolset and delegates all responsibility to it.

It is is a no-op by default, but you can subclass `WrapperToolset` to change the wrapped toolset's tool execution behavior by overriding the call_tool() method.

logging_toolset.py

```python
import asyncio

from typing_extensions import Any

from pydantic_ai import Agent, RunContext, ToolsetTool, WrapperToolset
from pydantic_ai.models.test import TestModel

from prepared_toolset import prepared_toolset

LOG = []

class LoggingToolset(WrapperToolset):
    async def call_tool(self, name: str, tool_args: dict[str, Any], ctx: RunContext, tool: ToolsetTool) -> Any:
        LOG.append(f'Calling tool {name!r} with args: {tool_args!r}')
        try:
            await asyncio.sleep(0.1 * len(LOG)) # (1)!

            result = await super().call_tool(name, tool_args, ctx, tool)
            LOG.append(f'Finished calling tool {name!r} with result: {result!r}')
        except Exception as e:
            LOG.append(f'Error calling tool {name!r}: {e}')
            raise e
        else:
            return result


logging_toolset = LoggingToolset(prepared_toolset)

agent = Agent(TestModel(), toolsets=[logging_toolset]) # (2)!
result = agent.run_sync('Call all the tools')
print(LOG)
"""
[
    "Calling tool 'temperature_celsius' with args: {'city': 'a'}",
    "Calling tool 'temperature_fahrenheit' with args: {'city': 'a'}",
    "Calling tool 'weather_conditions' with args: {'city': 'a'}",
    "Calling tool 'current_time' with args: {}",
    "Finished calling tool 'temperature_celsius' with result: 21.0",
    "Finished calling tool 'temperature_fahrenheit' with result: 69.8",
    'Finished calling tool \'weather_conditions\' with result: "It\'s raining"',
    "Finished calling tool 'current_time' with result: datetime.datetime(...)",
]
"""

```

1. All docs examples are tested in CI and their their output is verified, so we need `LOG` to always have the same order whenever this code is run. Since the tools could finish in any order, we sleep an increasing amount of time based on which number tool call we are to ensure that they finish (and log) in the same order they were called in.
1. We use TestModel here as it will automatically call each tool.

_(This example is complete, it can be run "as is")_
