### Agent Run Context and Dependencies

As workflows and activities run in separate processes, any values passed between them need to be serializable. As these payloads are stored in the workflow execution event history, Temporal limits their size to 2MB.

To account for these limitations, tool functions and the [event stream handler](#streaming) running inside activities receive a limited version of the agent's RunContext, and it's your responsibility to make sure that the [dependencies](../../dependencies/) object provided to TemporalAgent.run() can be serialized using Pydantic.

Specifically, only the `deps`, `run_id`, `retries`, `tool_call_id`, `tool_name`, `tool_call_approved`, `retry`, `max_retries`, `run_step`, `usage`, and `partial_output` fields are available by default, and trying to access `model`, `prompt`, `messages`, or `tracer` will raise an error. If you need one or more of these attributes to be available inside activities, you can create a TemporalRunContext subclass with custom `serialize_run_context` and `deserialize_run_context` class methods and pass it to TemporalAgent as `run_context_type`.
