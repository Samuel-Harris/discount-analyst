### Streaming

Because DBOS cannot stream output directly to the workflow or step call site, Agent.run_stream() and Agent.run_stream_events() are not supported when running inside of a DBOS workflow.

Instead, you can implement streaming by setting an event_stream_handler on the `Agent` or `DBOSAgent` instance and using DBOSAgent.run(). The event stream handler function will receive the agent run context and an async iterable of events from the model's streaming response and the agent's execution of tools. For examples, see the [streaming docs](../../agents/#streaming-all-events).
