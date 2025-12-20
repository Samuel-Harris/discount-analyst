## Task Configuration

You can customize Prefect task behavior, such as retries and timeouts, by passing TaskConfig objects to the `PrefectAgent` constructor:

- `mcp_task_config`: Configuration for MCP server communication tasks
- `model_task_config`: Configuration for model request tasks
- `tool_task_config`: Default configuration for all tool calls
- `tool_task_config_by_name`: Per-tool task configuration (overrides `tool_task_config`)
- `event_stream_handler_task_config`: Configuration for event stream handler tasks (applies when running inside a Prefect flow)

Available `TaskConfig` options:

- `retries`: Maximum number of retries for the task (default: `0`)
- `retry_delay_seconds`: Delay between retries in seconds (can be a single value or list for exponential backoff, default: `1.0`)
- `timeout_seconds`: Maximum time in seconds for the task to complete
- `cache_policy`: Custom Prefect cache policy for the task
- `persist_result`: Whether to persist the task result
- `result_storage`: Prefect result storage for the task (e.g., `'s3-bucket/my-storage'` or a `WritableFileSystem` block)
- `log_prints`: Whether to log print statements from the task (default: `False`)

Example:

prefect_agent_config.py

```python
from pydantic_ai import Agent
from pydantic_ai.durable_exec.prefect import PrefectAgent, TaskConfig

agent = Agent(
    'gpt-5',
    instructions="You're an expert in geography.",
    name='geography',
)

prefect_agent = PrefectAgent(
    agent,
    model_task_config=TaskConfig(
        retries=3,
        retry_delay_seconds=[1.0, 2.0, 4.0],  # Exponential backoff
        timeout_seconds=30.0,
    ),
)

async def main():
    result = await prefect_agent.run('What is the capital of France?')
    print(result.output)
    #> Paris

```

_(This example is complete, it can be run "as is" â€” you'll need to add `asyncio.run(main())` to run `main`)_
