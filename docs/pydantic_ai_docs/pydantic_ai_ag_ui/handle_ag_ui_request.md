### handle_ag_ui_request

```python
handle_ag_ui_request(
    agent: AbstractAgent[AgentDepsT, Any],
    request: Request,
    *,
    output_type: OutputSpec[Any] | None = None,
    message_history: Sequence[ModelMessage] | None = None,
    deferred_tool_results: (
        DeferredToolResults | None
    ) = None,
    model: Model | KnownModelName | str | None = None,
    deps: AgentDepsT = None,
    model_settings: ModelSettings | None = None,
    usage_limits: UsageLimits | None = None,
    usage: RunUsage | None = None,
    infer_name: bool = True,
    toolsets: (
        Sequence[AbstractToolset[AgentDepsT]] | None
    ) = None,
    on_complete: OnCompleteFunc[BaseEvent] | None = None
) -> Response

```

Handle an AG-UI request by running the agent and returning a streaming response.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `agent` | `AbstractAgent[AgentDepsT, Any]` | The agent to run. | _required_ | | `request` | `Request` | The Starlette request (e.g. from FastAPI) containing the AG-UI run input. | _required_ | | `output_type` | `OutputSpec[Any] | None` | Custom output type to use for this run, output_type may only be used if the agent has no output validators since output validators would expect an argument that matches the agent's output type. | `None` | | `message_history` | `Sequence[ModelMessage] | None` | History of the conversation so far. | `None` | | `deferred_tool_results` | `DeferredToolResults | None` | Optional results for deferred tool calls in the message history. | `None` | | `model` | `Model | KnownModelName | str | None` | Optional model to use for this run, required if model was not set when creating the agent. | `None` | | `deps` | `AgentDepsT` | Optional dependencies to use for this run. | `None` | | `model_settings` | `ModelSettings | None` | Optional settings to use for this model's request. | `None` | | `usage_limits` | `UsageLimits | None` | Optional limits on model request count or token usage. | `None` | | `usage` | `RunUsage | None` | Optional usage to start with, useful for resuming a conversation or agents used in tools. | `None` | | `infer_name` | `bool` | Whether to try to infer the agent name from the call frame if it's not set. | `True` | | `toolsets` | `Sequence[AbstractToolset[AgentDepsT]] | None` | Optional additional toolsets for this run. | `None` | | `on_complete` | `OnCompleteFunc[BaseEvent] | None` | Optional callback function called when the agent run completes successfully. The callback receives the completed AgentRunResult and can access all_messages() and other result data. | `None` |

Returns:

| Type | Description | | --- | --- | | `Response` | A streaming Starlette response with AG-UI protocol events. |

Source code in `pydantic_ai_slim/pydantic_ai/ag_ui.py`

```python
async def handle_ag_ui_request(
    agent: AbstractAgent[AgentDepsT, Any],
    request: Request,
    *,
    output_type: OutputSpec[Any] | None = None,
    message_history: Sequence[ModelMessage] | None = None,
    deferred_tool_results: DeferredToolResults | None = None,
    model: Model | KnownModelName | str | None = None,
    deps: AgentDepsT = None,
    model_settings: ModelSettings | None = None,
    usage_limits: UsageLimits | None = None,
    usage: RunUsage | None = None,
    infer_name: bool = True,
    toolsets: Sequence[AbstractToolset[AgentDepsT]] | None = None,
    on_complete: OnCompleteFunc[BaseEvent] | None = None,
) -> Response:
    """Handle an AG-UI request by running the agent and returning a streaming response.

    Args:
        agent: The agent to run.
        request: The Starlette request (e.g. from FastAPI) containing the AG-UI run input.

        output_type: Custom output type to use for this run, `output_type` may only be used if the agent has no
            output validators since output validators would expect an argument that matches the agent's output type.
        message_history: History of the conversation so far.
        deferred_tool_results: Optional results for deferred tool calls in the message history.
        model: Optional model to use for this run, required if `model` was not set when creating the agent.
        deps: Optional dependencies to use for this run.
        model_settings: Optional settings to use for this model's request.
        usage_limits: Optional limits on model request count or token usage.
        usage: Optional usage to start with, useful for resuming a conversation or agents used in tools.
        infer_name: Whether to try to infer the agent name from the call frame if it's not set.
        toolsets: Optional additional toolsets for this run.
        on_complete: Optional callback function called when the agent run completes successfully.
            The callback receives the completed [`AgentRunResult`][pydantic_ai.agent.AgentRunResult] and can access `all_messages()` and other result data.

    Returns:
        A streaming Starlette response with AG-UI protocol events.
    """
    return await AGUIAdapter[AgentDepsT].dispatch_request(
        request,
        agent=agent,
        deps=deps,
        output_type=output_type,
        message_history=message_history,
        deferred_tool_results=deferred_tool_results,
        model=model,
        model_settings=model_settings,
        usage_limits=usage_limits,
        usage=usage,
        infer_name=infer_name,
        toolsets=toolsets,
        on_complete=on_complete,
    )

```
