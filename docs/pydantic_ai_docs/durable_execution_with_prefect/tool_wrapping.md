### Tool Wrapping

Agent tools are automatically wrapped as Prefect tasks, which means they benefit from:

- **Retry logic**: Failed tool calls can be retried automatically
- **Caching**: Tool results are cached based on their inputs
- **Observability**: Tool execution is tracked in the Prefect UI

You can customize tool task behavior using `tool_task_config` (applies to all tools) or `tool_task_config_by_name` (per-tool configuration):

prefect_agent_config.py

```python
from pydantic_ai import Agent
from pydantic_ai.durable_exec.prefect import PrefectAgent, TaskConfig

agent = Agent('gpt-5', name='my_agent')

@agent.tool_plain
def fetch_data(url: str) -> str:
    # This tool will be wrapped as a Prefect task
    ...

prefect_agent = PrefectAgent(
    agent,
    tool_task_config=TaskConfig(retries=3),  # Default for all tools
    tool_task_config_by_name={
        'fetch_data': TaskConfig(timeout_seconds=10.0),  # Specific to fetch_data
        'simple_tool': None,  # Disable task wrapping for simple_tool
    },
)

```

Set a tool's config to `None` in `tool_task_config_by_name` to disable task wrapping for that specific tool.
