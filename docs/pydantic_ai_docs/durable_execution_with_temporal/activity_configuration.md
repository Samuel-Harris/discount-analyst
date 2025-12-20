## Activity Configuration

Temporal activity configuration, like timeouts and retry policies, can be customized by passing [`temporalio.workflow.ActivityConfig`](https://python.temporal.io/temporalio.workflow.ActivityConfig.html) objects to the `TemporalAgent` constructor:

- `activity_config`: The base Temporal activity config to use for all activities. If no config is provided, a `start_to_close_timeout` of 60 seconds is used.

- `model_activity_config`: The Temporal activity config to use for model request activities. This is merged with the base activity config.

- `toolset_activity_config`: The Temporal activity config to use for get-tools and call-tool activities for specific toolsets identified by ID. This is merged with the base activity config.

- `tool_activity_config`: The Temporal activity config to use for specific tool call activities identified by toolset ID and tool name. This is merged with the base and toolset-specific activity configs.

  If a tool does not use I/O, you can specify `False` to disable using an activity. Note that the tool is required to be defined as an `async` function as non-async tools are run in threads which are non-deterministic and thus not supported outside of activities.
