## Streamed Results

There two main challenges with streamed results:

1. Validating structured responses before they're complete, this is achieved by "partial validation" which was recently added to Pydantic in [pydantic/pydantic#10748](https://github.com/pydantic/pydantic/pull/10748).
1. When receiving a response, we don't know if it's the final response without starting to stream it and peeking at the content. Pydantic AI streams just enough of the response to sniff out if it's a tool call or an output, then streams the whole thing and calls tools, or returns the stream as a StreamedRunResult.

Note

As the `run_stream()` method will consider the first output matching the `output_type` to be the final output, it will stop running the agent graph and will not execute any tool calls made by the model after this "final" output.

If you want to always run the agent graph to completion and stream all events from the model's streaming response and the agent's execution of tools, use agent.run_stream_events() ([docs](../agents/#streaming-all-events)) or agent.iter() ([docs](../agents/#streaming-all-events-and-output)) instead.
