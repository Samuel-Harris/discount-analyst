A toolset represents a collection of [tools](../tools/) that can be registered with an agent in one go. They can be reused by different agents, swapped out at runtime or during testing, and composed in order to dynamically filter which tools are available, modify tool definitions, or change tool execution behavior. A toolset can contain locally defined functions, depend on an external service to provide them, or implement custom logic to list available tools and handle them being called.

Toolsets are used (among many other things) to define [MCP servers](../mcp/client/) available to an agent. Pydantic AI includes many kinds of toolsets which are described below, and you can define a [custom toolset](#building-a-custom-toolset) by inheriting from the AbstractToolset class.

The toolsets that will be available during an agent run can be specified in four different ways:

- at agent construction time, via the toolsets keyword argument to `Agent`, which takes toolset instances as well as functions that generate toolsets [dynamically](#dynamically-building-a-toolset) based on the agent run context
- at agent run time, via the `toolsets` keyword argument to agent.run(), agent.run_sync(), agent.run_stream(), or agent.iter(). These toolsets will be additional to those registered on the `Agent`
- [dynamically](#dynamically-building-a-toolset), via the @agent.toolset decorator which lets you build a toolset based on the agent run context
- as a contextual override, via the `toolsets` keyword argument to the agent.override() context manager. These toolsets will replace those provided at agent construction or run time during the life of the context manager

toolsets.py

```python
from pydantic_ai import Agent, FunctionToolset
from pydantic_ai.models.test import TestModel


def agent_tool():
    return "I'm registered directly on the agent"


def extra_tool():
    return "I'm passed as an extra tool for a specific run"


def override_tool():
    return 'I override all other tools'


agent_toolset = FunctionToolset(tools=[agent_tool]) # (1)!
extra_toolset = FunctionToolset(tools=[extra_tool])
override_toolset = FunctionToolset(tools=[override_tool])

test_model = TestModel() # (2)!
agent = Agent(test_model, toolsets=[agent_toolset])

result = agent.run_sync('What tools are available?')
print([t.name for t in test_model.last_model_request_parameters.function_tools])
#> ['agent_tool']

result = agent.run_sync('What tools are available?', toolsets=[extra_toolset])
print([t.name for t in test_model.last_model_request_parameters.function_tools])
#> ['agent_tool', 'extra_tool']

with agent.override(toolsets=[override_toolset]):
    result = agent.run_sync('What tools are available?', toolsets=[extra_toolset]) # (3)!
    print([t.name for t in test_model.last_model_request_parameters.function_tools])
    #> ['override_tool']

```

1. The FunctionToolset will be explained in detail in the next section.
1. We're using TestModel here because it makes it easy to see which tools were available on each run.
1. This `extra_toolset` will be ignored because we're inside an override context.

_(This example is complete, it can be run "as is")_
