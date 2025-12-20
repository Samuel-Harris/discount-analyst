### Parallel tool calls & concurrency

When a model returns multiple tool calls in one response, Pydantic AI schedules them concurrently using `asyncio.create_task`. If a tool requires sequential/serial execution, you can pass the sequential flag when registering the tool, or wrap the agent run in the with agent.sequential_tool_calls() context manager.

Async functions are run on the event loop, while sync functions are offloaded to threads. To get the best performance, _always_ use an async function _unless_ you're doing blocking I/O (and there's no way to use a non-blocking library instead) or CPU-bound work (like `numpy` or `scikit-learn` operations), so that simple functions are not offloaded to threads unnecessarily.

Limiting tool executions

You can cap tool executions within a run using [`UsageLimits(tool_calls_limit=...)`](../agents/#usage-limits). The counter increments only after a successful tool invocation. Output tools (used for [structured output](../output/)) are not counted in the `tool_calls` metric.
