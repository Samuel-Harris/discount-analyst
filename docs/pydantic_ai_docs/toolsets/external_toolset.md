## External Toolset

If your agent needs to be able to call [external tools](../deferred-tools/#external-tool-execution) that are provided and executed by an upstream service or frontend, you can build an ExternalToolset from a list of ToolDefinitions containing the tool names, arguments JSON schemas, and descriptions.

When the model calls an external tool, the call is considered to be ["deferred"](../deferred-tools/#deferred-tools), and the agent run will end with a DeferredToolRequests output object with a `calls` list holding ToolCallParts containing the tool name, validated arguments, and a unique tool call ID, which are expected to be passed to the upstream service or frontend that will produce the results.

When the tool call results are received from the upstream service or frontend, you can build a DeferredToolResults object with a `calls` dictionary that maps each tool call ID to an arbitrary value to be returned to the model, a [`ToolReturn`](../tools-advanced/#advanced-tool-returns) object, or a ModelRetry exception in case the tool call failed and the model should [try again](../tools-advanced/#tool-retries). This `DeferredToolResults` object can then be provided to one of the agent run methods as `deferred_tool_results`, alongside the original run's [message history](../message-history/).

Note that you need to add `DeferredToolRequests` to the `Agent`'s or `agent.run()`'s [`output_type`](../output/#structured-output) so that the possible types of the agent run output are correctly inferred. For more information, see the [Deferred Tools](../deferred-tools/#deferred-tools) documentation.

To demonstrate, let us first define a simple agent _without_ deferred tools:

[Learn about Gateway](../gateway) deferred_toolset_agent.py

```python
from pydantic import BaseModel

from pydantic_ai import Agent, FunctionToolset

toolset = FunctionToolset()


@toolset.tool
def get_default_language():
    return 'en-US'


@toolset.tool
def get_user_name():
    return 'David'


class PersonalizedGreeting(BaseModel):
    greeting: str
    language_code: str


agent = Agent('gateway/openai:gpt-5', toolsets=[toolset], output_type=PersonalizedGreeting)

result = agent.run_sync('Greet the user in a personalized way')
print(repr(result.output))
#> PersonalizedGreeting(greeting='Hello, David!', language_code='en-US')

```

deferred_toolset_agent.py

```python
from pydantic import BaseModel

from pydantic_ai import Agent, FunctionToolset

toolset = FunctionToolset()


@toolset.tool
def get_default_language():
    return 'en-US'


@toolset.tool
def get_user_name():
    return 'David'


class PersonalizedGreeting(BaseModel):
    greeting: str
    language_code: str


agent = Agent('openai:gpt-5', toolsets=[toolset], output_type=PersonalizedGreeting)

result = agent.run_sync('Greet the user in a personalized way')
print(repr(result.output))
#> PersonalizedGreeting(greeting='Hello, David!', language_code='en-US')

```

Next, let's define a function that represents a hypothetical "run agent" API endpoint that can be called by the frontend and takes a list of messages to send to the model, a list of frontend tool definitions, and optional deferred tool results. This is where `ExternalToolset`, `DeferredToolRequests`, and `DeferredToolResults` come in:

deferred_toolset_api.py

```python
from pydantic_ai import (
    DeferredToolRequests,
    DeferredToolResults,
    ExternalToolset,
    ModelMessage,
    ToolDefinition,
)

from deferred_toolset_agent import PersonalizedGreeting, agent


def run_agent(
    messages: list[ModelMessage] = [],
    frontend_tools: list[ToolDefinition] = {},
    deferred_tool_results: DeferredToolResults | None = None,
) -> tuple[PersonalizedGreeting | DeferredToolRequests, list[ModelMessage]]:
    deferred_toolset = ExternalToolset(frontend_tools)
    result = agent.run_sync(
        toolsets=[deferred_toolset], # (1)!
        output_type=[agent.output_type, DeferredToolRequests], # (2)!
        message_history=messages, # (3)!
        deferred_tool_results=deferred_tool_results,
    )
    return result.output, result.new_messages()

```

1. As mentioned in the [Deferred Tools](../deferred-tools/#deferred-tools) documentation, these `toolsets` are additional to those provided to the `Agent` constructor
1. As mentioned in the [Deferred Tools](../deferred-tools/#deferred-tools) documentation, this `output_type` overrides the one provided to the `Agent` constructor, so we have to make sure to not lose it
1. We don't include an `user_prompt` keyword argument as we expect the frontend to provide it via `messages`

Now, imagine that the code below is implemented on the frontend, and `run_agent` stands in for an API call to the backend that runs the agent. This is where we actually execute the deferred tool calls and start a new run with the new result included:

deferred_tools.py

```python
from pydantic_ai import (
    DeferredToolRequests,
    DeferredToolResults,
    ModelMessage,
    ModelRequest,
    ModelRetry,
    ToolDefinition,
    UserPromptPart,
)

from deferred_toolset_api import run_agent

frontend_tool_definitions = [
    ToolDefinition(
        name='get_preferred_language',
        parameters_json_schema={'type': 'object', 'properties': {'default_language': {'type': 'string'}}},
        description="Get the user's preferred language from their browser",
    )
]

def get_preferred_language(default_language: str) -> str:
    return 'es-MX' # (1)!

frontend_tool_functions = {'get_preferred_language': get_preferred_language}

messages: list[ModelMessage] = [
    ModelRequest(
        parts=[
            UserPromptPart(content='Greet the user in a personalized way')
        ]
    )
]

deferred_tool_results: DeferredToolResults | None = None

final_output = None
while True:
    output, new_messages = run_agent(messages, frontend_tool_definitions, deferred_tool_results)
    messages += new_messages

    if not isinstance(output, DeferredToolRequests):
        final_output = output
        break

    print(output.calls)
    """
    [
        ToolCallPart(
            tool_name='get_preferred_language',
            args={'default_language': 'en-US'},
            tool_call_id='pyd_ai_tool_call_id',
        )
    ]
    """
    deferred_tool_results = DeferredToolResults()
    for tool_call in output.calls:
        if function := frontend_tool_functions.get(tool_call.tool_name):
            result = function(**tool_call.args_as_dict())
        else:
            result = ModelRetry(f'Unknown tool {tool_call.tool_name!r}')
        deferred_tool_results.calls[tool_call.tool_call_id] = result

print(repr(final_output))
"""
PersonalizedGreeting(greeting='Hola, David! Espero que tengas un gran dÃ­a!', language_code='es-MX')
"""

```

1. Imagine that this returns the frontend [`navigator.language`](https://developer.mozilla.org/en-US/docs/Web/API/Navigator/language).

_(This example is complete, it can be run "as is")_
