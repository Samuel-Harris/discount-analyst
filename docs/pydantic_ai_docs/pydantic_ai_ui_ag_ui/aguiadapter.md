### AGUIAdapter

Bases: `UIAdapter[RunAgentInput, Message, BaseEvent, AgentDepsT, OutputDataT]`

UI adapter for the Agent-User Interaction (AG-UI) protocol.

Source code in `pydantic_ai_slim/pydantic_ai/ui/ag_ui/_adapter.py`

```python
class AGUIAdapter(UIAdapter[RunAgentInput, Message, BaseEvent, AgentDepsT, OutputDataT]):
    """UI adapter for the Agent-User Interaction (AG-UI) protocol."""

    @classmethod
    def build_run_input(cls, body: bytes) -> RunAgentInput:
        """Build an AG-UI run input object from the request body."""
        return RunAgentInput.model_validate_json(body)

    def build_event_stream(self) -> UIEventStream[RunAgentInput, BaseEvent, AgentDepsT, OutputDataT]:
        """Build an AG-UI event stream transformer."""
        return AGUIEventStream(self.run_input, accept=self.accept)

    @cached_property
    def messages(self) -> list[ModelMessage]:
        """Pydantic AI messages from the AG-UI run input."""
        return self.load_messages(self.run_input.messages)

    @cached_property
    def toolset(self) -> AbstractToolset[AgentDepsT] | None:
        """Toolset representing frontend tools from the AG-UI run input."""
        if self.run_input.tools:
            return _AGUIFrontendToolset[AgentDepsT](self.run_input.tools)
        return None

    @cached_property
    def state(self) -> dict[str, Any] | None:
        """Frontend state from the AG-UI run input."""
        state = self.run_input.state
        if state is None:
            return None

        if isinstance(state, Mapping) and not state:
            return None

        return cast('dict[str, Any]', state)

    @classmethod
    def load_messages(cls, messages: Sequence[Message]) -> list[ModelMessage]:
        """Transform AG-UI messages into Pydantic AI messages."""
        builder = MessagesBuilder()
        tool_calls: dict[str, str] = {}  # Tool call ID to tool name mapping.

        for msg in messages:
            if isinstance(msg, UserMessage | SystemMessage | DeveloperMessage) or (
                isinstance(msg, ToolMessage) and not msg.tool_call_id.startswith(BUILTIN_TOOL_CALL_ID_PREFIX)
            ):
                if isinstance(msg, UserMessage):
                    builder.add(UserPromptPart(content=msg.content))
                elif isinstance(msg, SystemMessage | DeveloperMessage):
                    builder.add(SystemPromptPart(content=msg.content))
                else:
                    tool_call_id = msg.tool_call_id
                    tool_name = tool_calls.get(tool_call_id)
                    if tool_name is None:  # pragma: no cover
                        raise ValueError(f'Tool call with ID {tool_call_id} not found in the history.')

                    builder.add(
                        ToolReturnPart(
                            tool_name=tool_name,
                            content=msg.content,
                            tool_call_id=tool_call_id,
                        )
                    )

            elif isinstance(msg, AssistantMessage) or (  # pragma: no branch
                isinstance(msg, ToolMessage) and msg.tool_call_id.startswith(BUILTIN_TOOL_CALL_ID_PREFIX)
            ):
                if isinstance(msg, AssistantMessage):
                    if msg.content:
                        builder.add(TextPart(content=msg.content))

                    if msg.tool_calls:
                        for tool_call in msg.tool_calls:
                            tool_call_id = tool_call.id
                            tool_name = tool_call.function.name
                            tool_calls[tool_call_id] = tool_name

                            if tool_call_id.startswith(BUILTIN_TOOL_CALL_ID_PREFIX):
                                _, provider_name, tool_call_id = tool_call_id.split('|', 2)
                                builder.add(
                                    BuiltinToolCallPart(
                                        tool_name=tool_name,
                                        args=tool_call.function.arguments,
                                        tool_call_id=tool_call_id,
                                        provider_name=provider_name,
                                    )
                                )
                            else:
                                builder.add(
                                    ToolCallPart(
                                        tool_name=tool_name,
                                        tool_call_id=tool_call_id,
                                        args=tool_call.function.arguments,
                                    )
                                )
                else:
                    tool_call_id = msg.tool_call_id
                    tool_name = tool_calls.get(tool_call_id)
                    if tool_name is None:  # pragma: no cover
                        raise ValueError(f'Tool call with ID {tool_call_id} not found in the history.')
                    _, provider_name, tool_call_id = tool_call_id.split('|', 2)

                    builder.add(
                        BuiltinToolReturnPart(
                            tool_name=tool_name,
                            content=msg.content,
                            tool_call_id=tool_call_id,
                            provider_name=provider_name,
                        )
                    )

        return builder.messages

```

#### build_run_input

```python
build_run_input(body: bytes) -> RunAgentInput

```

Build an AG-UI run input object from the request body.

Source code in `pydantic_ai_slim/pydantic_ai/ui/ag_ui/_adapter.py`

```python
@classmethod
def build_run_input(cls, body: bytes) -> RunAgentInput:
    """Build an AG-UI run input object from the request body."""
    return RunAgentInput.model_validate_json(body)

```

#### build_event_stream

```python
build_event_stream() -> (
    UIEventStream[
        RunAgentInput, BaseEvent, AgentDepsT, OutputDataT
    ]
)

```

Build an AG-UI event stream transformer.

Source code in `pydantic_ai_slim/pydantic_ai/ui/ag_ui/_adapter.py`

```python
def build_event_stream(self) -> UIEventStream[RunAgentInput, BaseEvent, AgentDepsT, OutputDataT]:
    """Build an AG-UI event stream transformer."""
    return AGUIEventStream(self.run_input, accept=self.accept)

```

#### messages

```python
messages: list[ModelMessage]

```

Pydantic AI messages from the AG-UI run input.

#### toolset

```python
toolset: AbstractToolset[AgentDepsT] | None

```

Toolset representing frontend tools from the AG-UI run input.

#### state

```python
state: dict[str, Any] | None

```

Frontend state from the AG-UI run input.

#### load_messages

```python
load_messages(
    messages: Sequence[Message],
) -> list[ModelMessage]

```

Transform AG-UI messages into Pydantic AI messages.

Source code in `pydantic_ai_slim/pydantic_ai/ui/ag_ui/_adapter.py`

```python
@classmethod
def load_messages(cls, messages: Sequence[Message]) -> list[ModelMessage]:
    """Transform AG-UI messages into Pydantic AI messages."""
    builder = MessagesBuilder()
    tool_calls: dict[str, str] = {}  # Tool call ID to tool name mapping.

    for msg in messages:
        if isinstance(msg, UserMessage | SystemMessage | DeveloperMessage) or (
            isinstance(msg, ToolMessage) and not msg.tool_call_id.startswith(BUILTIN_TOOL_CALL_ID_PREFIX)
        ):
            if isinstance(msg, UserMessage):
                builder.add(UserPromptPart(content=msg.content))
            elif isinstance(msg, SystemMessage | DeveloperMessage):
                builder.add(SystemPromptPart(content=msg.content))
            else:
                tool_call_id = msg.tool_call_id
                tool_name = tool_calls.get(tool_call_id)
                if tool_name is None:  # pragma: no cover
                    raise ValueError(f'Tool call with ID {tool_call_id} not found in the history.')

                builder.add(
                    ToolReturnPart(
                        tool_name=tool_name,
                        content=msg.content,
                        tool_call_id=tool_call_id,
                    )
                )

        elif isinstance(msg, AssistantMessage) or (  # pragma: no branch
            isinstance(msg, ToolMessage) and msg.tool_call_id.startswith(BUILTIN_TOOL_CALL_ID_PREFIX)
        ):
            if isinstance(msg, AssistantMessage):
                if msg.content:
                    builder.add(TextPart(content=msg.content))

                if msg.tool_calls:
                    for tool_call in msg.tool_calls:
                        tool_call_id = tool_call.id
                        tool_name = tool_call.function.name
                        tool_calls[tool_call_id] = tool_name

                        if tool_call_id.startswith(BUILTIN_TOOL_CALL_ID_PREFIX):
                            _, provider_name, tool_call_id = tool_call_id.split('|', 2)
                            builder.add(
                                BuiltinToolCallPart(
                                    tool_name=tool_name,
                                    args=tool_call.function.arguments,
                                    tool_call_id=tool_call_id,
                                    provider_name=provider_name,
                                )
                            )
                        else:
                            builder.add(
                                ToolCallPart(
                                    tool_name=tool_name,
                                    tool_call_id=tool_call_id,
                                    args=tool_call.function.arguments,
                                )
                            )
            else:
                tool_call_id = msg.tool_call_id
                tool_name = tool_calls.get(tool_call_id)
                if tool_name is None:  # pragma: no cover
                    raise ValueError(f'Tool call with ID {tool_call_id} not found in the history.')
                _, provider_name, tool_call_id = tool_call_id.split('|', 2)

                builder.add(
                    BuiltinToolReturnPart(
                        tool_name=tool_name,
                        content=msg.content,
                        tool_call_id=tool_call_id,
                        provider_name=provider_name,
                    )
                )

    return builder.messages

```
