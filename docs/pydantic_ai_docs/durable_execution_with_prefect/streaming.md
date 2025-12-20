### Streaming

When running inside a Prefect flow, Agent.run_stream() works but doesn't provide real-time streaming because Prefect tasks consume their entire execution before returning results. The method will execute fully and return the complete result at once.

For real-time streaming behavior inside Prefect flows, you can set an event_stream_handler on the `Agent` or `PrefectAgent` instance and use PrefectAgent.run().

**Note**: Event stream handlers behave differently when running inside a Prefect flow versus outside:

- **Outside a flow**: The handler receives events as they stream from the model
- **Inside a flow**: Each event is wrapped as a Prefect task for durability, which may affect timing but ensures reliability

The event stream handler function will receive the agent run context and an async iterable of events from the model's streaming response and the agent's execution of tools. For examples, see the [streaming docs](../../agents/#streaming-all-events).
