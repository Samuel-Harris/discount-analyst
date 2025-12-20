### Streaming

Because Temporal activities cannot stream output directly to the activity call site, Agent.run_stream(), Agent.run_stream_events(), and Agent.iter() are not supported.

Instead, you can implement streaming by setting an event_stream_handler on the `Agent` or `TemporalAgent` instance and using TemporalAgent.run() inside the workflow. The event stream handler function will receive the agent run context and an async iterable of events from the model's streaming response and the agent's execution of tools. For examples, see the [streaming docs](../../agents/#streaming-all-events).

As the streaming model request activity, workflow, and workflow execution call all take place in separate processes, passing data between them requires some care:

- To get data from the workflow call site or workflow to the event stream handler, you can use a [dependencies object](#agent-run-context-and-dependencies).
- To get data from the event stream handler to the workflow, workflow call site, or a frontend, you need to use an external system that the event stream handler can write to and the event consumer can read from, like a message queue. You can use the dependency object to make sure the same connection string or other unique ID is available in all the places that need it.
