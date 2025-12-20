### Requiring Tool Approval

ApprovalRequiredToolset wraps a toolset and lets you dynamically [require approval](../deferred-tools/#human-in-the-loop-tool-approval) for a given tool call based on a user-defined function that is passed the agent run context, the tool's ToolDefinition, and the validated tool call arguments. If no function is provided, all tool calls will require approval.

To easily chain different modifications, you can also call approval_required() on any toolset instead of directly constructing a `ApprovalRequiredToolset`.

See the [Human-in-the-Loop Tool Approval](../deferred-tools/#human-in-the-loop-tool-approval) documentation for more information on how to handle agent runs that call tools that require approval and how to pass in the results.

approval_required_toolset.py

```python
from pydantic_ai import Agent, DeferredToolRequests, DeferredToolResults
from pydantic_ai.models.test import TestModel

from prepared_toolset import prepared_toolset

approval_required_toolset = prepared_toolset.approval_required(lambda ctx, tool_def, tool_args: tool_def.name.startswith('temperature'))

test_model = TestModel(call_tools=['temperature_celsius', 'temperature_fahrenheit']) # (1)!
agent = Agent(
    test_model,
    toolsets=[approval_required_toolset],
    output_type=[str, DeferredToolRequests],
)
result = agent.run_sync('Call the temperature tools')
messages = result.all_messages()
print(result.output)
"""
DeferredToolRequests(
    calls=[],
    approvals=[
        ToolCallPart(
            tool_name='temperature_celsius',
            args={'city': 'a'},
            tool_call_id='pyd_ai_tool_call_id__temperature_celsius',
        ),
        ToolCallPart(
            tool_name='temperature_fahrenheit',
            args={'city': 'a'},
            tool_call_id='pyd_ai_tool_call_id__temperature_fahrenheit',
        ),
    ],
    metadata={},
)
"""

result = agent.run_sync(
    message_history=messages,
    deferred_tool_results=DeferredToolResults(
        approvals={
            'pyd_ai_tool_call_id__temperature_celsius': True,
            'pyd_ai_tool_call_id__temperature_fahrenheit': False,
        }
    )
)
print(result.output)
#> {"temperature_celsius":21.0,"temperature_fahrenheit":"The tool call was denied."}

```

1. We're using TestModel here because it makes it easy to specify which tools to call.

_(This example is complete, it can be run "as is")_
