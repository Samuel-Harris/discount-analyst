### AgentRunResult

Bases: `Generic[OutputDataT]`

The final result of an agent run.

Source code in `pydantic_ai_slim/pydantic_ai/run.py`

```python
@dataclasses.dataclass
class AgentRunResult(Generic[OutputDataT]):
    """The final result of an agent run."""

    output: OutputDataT
    """The output data from the agent run."""

    _output_tool_name: str | None = dataclasses.field(repr=False, compare=False, default=None)
    _state: _agent_graph.GraphAgentState = dataclasses.field(
        repr=False, compare=False, default_factory=_agent_graph.GraphAgentState
    )
    _new_message_index: int = dataclasses.field(repr=False, compare=False, default=0)
    _traceparent_value: str | None = dataclasses.field(repr=False, compare=False, default=None)

    @overload
    def _traceparent(self, *, required: Literal[False]) -> str | None: ...
    @overload
    def _traceparent(self) -> str: ...
    def _traceparent(self, *, required: bool = True) -> str | None:
        if self._traceparent_value is None and required:  # pragma: no cover
            raise AttributeError('No span was created for this agent run')
        return self._traceparent_value

    def _set_output_tool_return(self, return_content: str) -> list[_messages.ModelMessage]:
        """Set return content for the output tool.

        Useful if you want to continue the conversation and want to set the response to the output tool call.
        """
        if not self._output_tool_name:
            raise ValueError('Cannot set output tool return content when the return type is `str`.')

        messages = self._state.message_history
        last_message = messages[-1]
        for idx, part in enumerate(last_message.parts):
            if isinstance(part, _messages.ToolReturnPart) and part.tool_name == self._output_tool_name:
                # Only do deepcopy when we have to modify
                copied_messages = list(messages)
                copied_last = deepcopy(last_message)
                copied_last.parts[idx].content = return_content  # type: ignore[misc]
                copied_messages[-1] = copied_last
                return copied_messages

        raise LookupError(f'No tool call found with tool name {self._output_tool_name!r}.')

    def all_messages(self, *, output_tool_return_content: str | None = None) -> list[_messages.ModelMessage]:
        """Return the history of _messages.

        Args:
            output_tool_return_content: The return content of the tool call to set in the last message.
                This provides a convenient way to modify the content of the output tool call if you want to continue
                the conversation and want to set the response to the output tool call. If `None`, the last message will
                not be modified.

        Returns:
            List of messages.
        """
        if output_tool_return_content is not None:
            return self._set_output_tool_return(output_tool_return_content)
        else:
            return self._state.message_history

    def all_messages_json(self, *, output_tool_return_content: str | None = None) -> bytes:
        """Return all messages from [`all_messages`][pydantic_ai.agent.AgentRunResult.all_messages] as JSON bytes.

        Args:
            output_tool_return_content: The return content of the tool call to set in the last message.
                This provides a convenient way to modify the content of the output tool call if you want to continue
                the conversation and want to set the response to the output tool call. If `None`, the last message will
                not be modified.

        Returns:
            JSON bytes representing the messages.
        """
        return _messages.ModelMessagesTypeAdapter.dump_json(
            self.all_messages(output_tool_return_content=output_tool_return_content)
        )

    def new_messages(self, *, output_tool_return_content: str | None = None) -> list[_messages.ModelMessage]:
        """Return new messages associated with this run.

        Messages from older runs are excluded.

        Args:
            output_tool_return_content: The return content of the tool call to set in the last message.
                This provides a convenient way to modify the content of the output tool call if you want to continue
                the conversation and want to set the response to the output tool call. If `None`, the last message will
                not be modified.

        Returns:
            List of new messages.
        """
        return self.all_messages(output_tool_return_content=output_tool_return_content)[self._new_message_index :]

    def new_messages_json(self, *, output_tool_return_content: str | None = None) -> bytes:
        """Return new messages from [`new_messages`][pydantic_ai.agent.AgentRunResult.new_messages] as JSON bytes.

        Args:
            output_tool_return_content: The return content of the tool call to set in the last message.
                This provides a convenient way to modify the content of the output tool call if you want to continue
                the conversation and want to set the response to the output tool call. If `None`, the last message will
                not be modified.

        Returns:
            JSON bytes representing the new messages.
        """
        return _messages.ModelMessagesTypeAdapter.dump_json(
            self.new_messages(output_tool_return_content=output_tool_return_content)
        )

    @property
    def response(self) -> _messages.ModelResponse:
        """Return the last response from the message history."""
        # The response may not be the very last item if it contained an output tool call. See `CallToolsNode._handle_final_result`.
        for message in reversed(self.all_messages()):
            if isinstance(message, _messages.ModelResponse):
                return message
        raise ValueError('No response found in the message history')  # pragma: no cover

    # TODO (v2): Make this a property
    def usage(self) -> _usage.RunUsage:
        """Return the usage of the whole run."""
        return self._state.usage

    # TODO (v2): Make this a property
    def timestamp(self) -> datetime:
        """Return the timestamp of last response."""
        return self.response.timestamp

    @property
    def run_id(self) -> str:
        """The unique identifier for the agent run."""
        return self._state.run_id

```

#### output

```python
output: OutputDataT

```

The output data from the agent run.

#### all_messages

```python
all_messages(
    *, output_tool_return_content: str | None = None
) -> list[ModelMessage]

```

Return the history of \_messages.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `output_tool_return_content` | `str | None` | The return content of the tool call to set in the last message. This provides a convenient way to modify the content of the output tool call if you want to continue the conversation and want to set the response to the output tool call. If None, the last message will not be modified. | `None` |

Returns:

| Type | Description | | --- | --- | | `list[ModelMessage]` | List of messages. |

Source code in `pydantic_ai_slim/pydantic_ai/run.py`

```python
def all_messages(self, *, output_tool_return_content: str | None = None) -> list[_messages.ModelMessage]:
    """Return the history of _messages.

    Args:
        output_tool_return_content: The return content of the tool call to set in the last message.
            This provides a convenient way to modify the content of the output tool call if you want to continue
            the conversation and want to set the response to the output tool call. If `None`, the last message will
            not be modified.

    Returns:
        List of messages.
    """
    if output_tool_return_content is not None:
        return self._set_output_tool_return(output_tool_return_content)
    else:
        return self._state.message_history

```

#### all_messages_json

```python
all_messages_json(
    *, output_tool_return_content: str | None = None
) -> bytes

```

Return all messages from all_messages as JSON bytes.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `output_tool_return_content` | `str | None` | The return content of the tool call to set in the last message. This provides a convenient way to modify the content of the output tool call if you want to continue the conversation and want to set the response to the output tool call. If None, the last message will not be modified. | `None` |

Returns:

| Type | Description | | --- | --- | | `bytes` | JSON bytes representing the messages. |

Source code in `pydantic_ai_slim/pydantic_ai/run.py`

```python
def all_messages_json(self, *, output_tool_return_content: str | None = None) -> bytes:
    """Return all messages from [`all_messages`][pydantic_ai.agent.AgentRunResult.all_messages] as JSON bytes.

    Args:
        output_tool_return_content: The return content of the tool call to set in the last message.
            This provides a convenient way to modify the content of the output tool call if you want to continue
            the conversation and want to set the response to the output tool call. If `None`, the last message will
            not be modified.

    Returns:
        JSON bytes representing the messages.
    """
    return _messages.ModelMessagesTypeAdapter.dump_json(
        self.all_messages(output_tool_return_content=output_tool_return_content)
    )

```

#### new_messages

```python
new_messages(
    *, output_tool_return_content: str | None = None
) -> list[ModelMessage]

```

Return new messages associated with this run.

Messages from older runs are excluded.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `output_tool_return_content` | `str | None` | The return content of the tool call to set in the last message. This provides a convenient way to modify the content of the output tool call if you want to continue the conversation and want to set the response to the output tool call. If None, the last message will not be modified. | `None` |

Returns:

| Type | Description | | --- | --- | | `list[ModelMessage]` | List of new messages. |

Source code in `pydantic_ai_slim/pydantic_ai/run.py`

```python
def new_messages(self, *, output_tool_return_content: str | None = None) -> list[_messages.ModelMessage]:
    """Return new messages associated with this run.

    Messages from older runs are excluded.

    Args:
        output_tool_return_content: The return content of the tool call to set in the last message.
            This provides a convenient way to modify the content of the output tool call if you want to continue
            the conversation and want to set the response to the output tool call. If `None`, the last message will
            not be modified.

    Returns:
        List of new messages.
    """
    return self.all_messages(output_tool_return_content=output_tool_return_content)[self._new_message_index :]

```

#### new_messages_json

```python
new_messages_json(
    *, output_tool_return_content: str | None = None
) -> bytes

```

Return new messages from new_messages as JSON bytes.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `output_tool_return_content` | `str | None` | The return content of the tool call to set in the last message. This provides a convenient way to modify the content of the output tool call if you want to continue the conversation and want to set the response to the output tool call. If None, the last message will not be modified. | `None` |

Returns:

| Type | Description | | --- | --- | | `bytes` | JSON bytes representing the new messages. |

Source code in `pydantic_ai_slim/pydantic_ai/run.py`

```python
def new_messages_json(self, *, output_tool_return_content: str | None = None) -> bytes:
    """Return new messages from [`new_messages`][pydantic_ai.agent.AgentRunResult.new_messages] as JSON bytes.

    Args:
        output_tool_return_content: The return content of the tool call to set in the last message.
            This provides a convenient way to modify the content of the output tool call if you want to continue
            the conversation and want to set the response to the output tool call. If `None`, the last message will
            not be modified.

    Returns:
        JSON bytes representing the new messages.
    """
    return _messages.ModelMessagesTypeAdapter.dump_json(
        self.new_messages(output_tool_return_content=output_tool_return_content)
    )

```

#### response

```python
response: ModelResponse

```

Return the last response from the message history.

#### usage

```python
usage() -> RunUsage

```

Return the usage of the whole run.

Source code in `pydantic_ai_slim/pydantic_ai/run.py`

```python
def usage(self) -> _usage.RunUsage:
    """Return the usage of the whole run."""
    return self._state.usage

```

#### timestamp

```python
timestamp() -> datetime

```

Return the timestamp of last response.

Source code in `pydantic_ai_slim/pydantic_ai/run.py`

```python
def timestamp(self) -> datetime:
    """Return the timestamp of last response."""
    return self.response.timestamp

```

#### run_id

```python
run_id: str

```

The unique identifier for the agent run.
