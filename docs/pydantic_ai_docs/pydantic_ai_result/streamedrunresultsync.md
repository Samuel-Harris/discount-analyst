### StreamedRunResultSync

Bases: `Generic[AgentDepsT, OutputDataT]`

Synchronous wrapper for StreamedRunResult that only exposes sync methods.

Source code in `pydantic_ai_slim/pydantic_ai/result.py`

```python
@dataclass(init=False)
class StreamedRunResultSync(Generic[AgentDepsT, OutputDataT]):
    """Synchronous wrapper for [`StreamedRunResult`][pydantic_ai.result.StreamedRunResult] that only exposes sync methods."""

    _streamed_run_result: StreamedRunResult[AgentDepsT, OutputDataT]

    def __init__(self, streamed_run_result: StreamedRunResult[AgentDepsT, OutputDataT]) -> None:
        self._streamed_run_result = streamed_run_result

    def all_messages(self, *, output_tool_return_content: str | None = None) -> list[_messages.ModelMessage]:
        """Return the history of messages.

        Args:
            output_tool_return_content: The return content of the tool call to set in the last message.
                This provides a convenient way to modify the content of the output tool call if you want to continue
                the conversation and want to set the response to the output tool call. If `None`, the last message will
                not be modified.

        Returns:
            List of messages.
        """
        return self._streamed_run_result.all_messages(output_tool_return_content=output_tool_return_content)

    def all_messages_json(self, *, output_tool_return_content: str | None = None) -> bytes:  # pragma: no cover
        """Return all messages from [`all_messages`][pydantic_ai.result.StreamedRunResultSync.all_messages] as JSON bytes.

        Args:
            output_tool_return_content: The return content of the tool call to set in the last message.
                This provides a convenient way to modify the content of the output tool call if you want to continue
                the conversation and want to set the response to the output tool call. If `None`, the last message will
                not be modified.

        Returns:
            JSON bytes representing the messages.
        """
        return self._streamed_run_result.all_messages_json(output_tool_return_content=output_tool_return_content)

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
        return self._streamed_run_result.new_messages(output_tool_return_content=output_tool_return_content)

    def new_messages_json(self, *, output_tool_return_content: str | None = None) -> bytes:  # pragma: no cover
        """Return new messages from [`new_messages`][pydantic_ai.result.StreamedRunResultSync.new_messages] as JSON bytes.

        Args:
            output_tool_return_content: The return content of the tool call to set in the last message.
                This provides a convenient way to modify the content of the output tool call if you want to continue
                the conversation and want to set the response to the output tool call. If `None`, the last message will
                not be modified.

        Returns:
            JSON bytes representing the new messages.
        """
        return self._streamed_run_result.new_messages_json(output_tool_return_content=output_tool_return_content)

    def stream_output(self, *, debounce_by: float | None = 0.1) -> Iterator[OutputDataT]:
        """Stream the output as an iterable.

        The pydantic validator for structured data will be called in
        [partial mode](https://docs.pydantic.dev/dev/concepts/experimental/#partial-validation)
        on each iteration.

        Args:
            debounce_by: by how much (if at all) to debounce/group the output chunks by. `None` means no debouncing.
                Debouncing is particularly important for long structured outputs to reduce the overhead of
                performing validation as each token is received.

        Returns:
            An iterable of the response data.
        """
        return _utils.sync_async_iterator(self._streamed_run_result.stream_output(debounce_by=debounce_by))

    def stream_text(self, *, delta: bool = False, debounce_by: float | None = 0.1) -> Iterator[str]:
        """Stream the text result as an iterable.

        !!! note
            Result validators will NOT be called on the text result if `delta=True`.

        Args:
            delta: if `True`, yield each chunk of text as it is received, if `False` (default), yield the full text
                up to the current point.
            debounce_by: by how much (if at all) to debounce/group the response chunks by. `None` means no debouncing.
                Debouncing is particularly important for long structured responses to reduce the overhead of
                performing validation as each token is received.
        """
        return _utils.sync_async_iterator(self._streamed_run_result.stream_text(delta=delta, debounce_by=debounce_by))

    def stream_responses(self, *, debounce_by: float | None = 0.1) -> Iterator[tuple[_messages.ModelResponse, bool]]:
        """Stream the response as an iterable of Structured LLM Messages.

        Args:
            debounce_by: by how much (if at all) to debounce/group the response chunks by. `None` means no debouncing.
                Debouncing is particularly important for long structured responses to reduce the overhead of
                performing validation as each token is received.

        Returns:
            An iterable of the structured response message and whether that is the last message.
        """
        return _utils.sync_async_iterator(self._streamed_run_result.stream_responses(debounce_by=debounce_by))

    def get_output(self) -> OutputDataT:
        """Stream the whole response, validate and return it."""
        return _utils.get_event_loop().run_until_complete(self._streamed_run_result.get_output())

    @property
    def response(self) -> _messages.ModelResponse:
        """Return the current state of the response."""
        return self._streamed_run_result.response

    def usage(self) -> RunUsage:
        """Return the usage of the whole run.

        !!! note
            This won't return the full usage until the stream is finished.
        """
        return self._streamed_run_result.usage()

    def timestamp(self) -> datetime:
        """Get the timestamp of the response."""
        return self._streamed_run_result.timestamp()

    @property
    def run_id(self) -> str:
        """The unique identifier for the agent run."""
        return self._streamed_run_result.run_id

    def validate_response_output(self, message: _messages.ModelResponse, *, allow_partial: bool = False) -> OutputDataT:
        """Validate a structured result message."""
        return _utils.get_event_loop().run_until_complete(
            self._streamed_run_result.validate_response_output(message, allow_partial=allow_partial)
        )

    @property
    def is_complete(self) -> bool:
        """Whether the stream has all been received.

        This is set to `True` when one of
        [`stream_output`][pydantic_ai.result.StreamedRunResultSync.stream_output],
        [`stream_text`][pydantic_ai.result.StreamedRunResultSync.stream_text],
        [`stream_responses`][pydantic_ai.result.StreamedRunResultSync.stream_responses] or
        [`get_output`][pydantic_ai.result.StreamedRunResultSync.get_output] completes.
        """
        return self._streamed_run_result.is_complete

```

#### all_messages

```python
all_messages(
    *, output_tool_return_content: str | None = None
) -> list[ModelMessage]

```

Return the history of messages.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `output_tool_return_content` | `str | None` | The return content of the tool call to set in the last message. This provides a convenient way to modify the content of the output tool call if you want to continue the conversation and want to set the response to the output tool call. If None, the last message will not be modified. | `None` |

Returns:

| Type | Description | | --- | --- | | `list[ModelMessage]` | List of messages. |

Source code in `pydantic_ai_slim/pydantic_ai/result.py`

```python
def all_messages(self, *, output_tool_return_content: str | None = None) -> list[_messages.ModelMessage]:
    """Return the history of messages.

    Args:
        output_tool_return_content: The return content of the tool call to set in the last message.
            This provides a convenient way to modify the content of the output tool call if you want to continue
            the conversation and want to set the response to the output tool call. If `None`, the last message will
            not be modified.

    Returns:
        List of messages.
    """
    return self._streamed_run_result.all_messages(output_tool_return_content=output_tool_return_content)

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

Source code in `pydantic_ai_slim/pydantic_ai/result.py`

```python
def all_messages_json(self, *, output_tool_return_content: str | None = None) -> bytes:  # pragma: no cover
    """Return all messages from [`all_messages`][pydantic_ai.result.StreamedRunResultSync.all_messages] as JSON bytes.

    Args:
        output_tool_return_content: The return content of the tool call to set in the last message.
            This provides a convenient way to modify the content of the output tool call if you want to continue
            the conversation and want to set the response to the output tool call. If `None`, the last message will
            not be modified.

    Returns:
        JSON bytes representing the messages.
    """
    return self._streamed_run_result.all_messages_json(output_tool_return_content=output_tool_return_content)

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

Source code in `pydantic_ai_slim/pydantic_ai/result.py`

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
    return self._streamed_run_result.new_messages(output_tool_return_content=output_tool_return_content)

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

Source code in `pydantic_ai_slim/pydantic_ai/result.py`

```python
def new_messages_json(self, *, output_tool_return_content: str | None = None) -> bytes:  # pragma: no cover
    """Return new messages from [`new_messages`][pydantic_ai.result.StreamedRunResultSync.new_messages] as JSON bytes.

    Args:
        output_tool_return_content: The return content of the tool call to set in the last message.
            This provides a convenient way to modify the content of the output tool call if you want to continue
            the conversation and want to set the response to the output tool call. If `None`, the last message will
            not be modified.

    Returns:
        JSON bytes representing the new messages.
    """
    return self._streamed_run_result.new_messages_json(output_tool_return_content=output_tool_return_content)

```

#### stream_output

```python
stream_output(
    *, debounce_by: float | None = 0.1
) -> Iterator[OutputDataT]

```

Stream the output as an iterable.

The pydantic validator for structured data will be called in [partial mode](https://docs.pydantic.dev/dev/concepts/experimental/#partial-validation) on each iteration.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `debounce_by` | `float | None` | by how much (if at all) to debounce/group the output chunks by. None means no debouncing. Debouncing is particularly important for long structured outputs to reduce the overhead of performing validation as each token is received. | `0.1` |

Returns:

| Type | Description | | --- | --- | | `Iterator[OutputDataT]` | An iterable of the response data. |

Source code in `pydantic_ai_slim/pydantic_ai/result.py`

```python
def stream_output(self, *, debounce_by: float | None = 0.1) -> Iterator[OutputDataT]:
    """Stream the output as an iterable.

    The pydantic validator for structured data will be called in
    [partial mode](https://docs.pydantic.dev/dev/concepts/experimental/#partial-validation)
    on each iteration.

    Args:
        debounce_by: by how much (if at all) to debounce/group the output chunks by. `None` means no debouncing.
            Debouncing is particularly important for long structured outputs to reduce the overhead of
            performing validation as each token is received.

    Returns:
        An iterable of the response data.
    """
    return _utils.sync_async_iterator(self._streamed_run_result.stream_output(debounce_by=debounce_by))

```

#### stream_text

```python
stream_text(
    *, delta: bool = False, debounce_by: float | None = 0.1
) -> Iterator[str]

```

Stream the text result as an iterable.

Note

Result validators will NOT be called on the text result if `delta=True`.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `delta` | `bool` | if True, yield each chunk of text as it is received, if False (default), yield the full text up to the current point. | `False` | | `debounce_by` | `float | None` | by how much (if at all) to debounce/group the response chunks by. None means no debouncing. Debouncing is particularly important for long structured responses to reduce the overhead of performing validation as each token is received. | `0.1` |

Source code in `pydantic_ai_slim/pydantic_ai/result.py`

```python
def stream_text(self, *, delta: bool = False, debounce_by: float | None = 0.1) -> Iterator[str]:
    """Stream the text result as an iterable.

    !!! note
        Result validators will NOT be called on the text result if `delta=True`.

    Args:
        delta: if `True`, yield each chunk of text as it is received, if `False` (default), yield the full text
            up to the current point.
        debounce_by: by how much (if at all) to debounce/group the response chunks by. `None` means no debouncing.
            Debouncing is particularly important for long structured responses to reduce the overhead of
            performing validation as each token is received.
    """
    return _utils.sync_async_iterator(self._streamed_run_result.stream_text(delta=delta, debounce_by=debounce_by))

```

#### stream_responses

```python
stream_responses(
    *, debounce_by: float | None = 0.1
) -> Iterator[tuple[ModelResponse, bool]]

```

Stream the response as an iterable of Structured LLM Messages.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `debounce_by` | `float | None` | by how much (if at all) to debounce/group the response chunks by. None means no debouncing. Debouncing is particularly important for long structured responses to reduce the overhead of performing validation as each token is received. | `0.1` |

Returns:

| Type | Description | | --- | --- | | `Iterator[tuple[ModelResponse, bool]]` | An iterable of the structured response message and whether that is the last message. |

Source code in `pydantic_ai_slim/pydantic_ai/result.py`

```python
def stream_responses(self, *, debounce_by: float | None = 0.1) -> Iterator[tuple[_messages.ModelResponse, bool]]:
    """Stream the response as an iterable of Structured LLM Messages.

    Args:
        debounce_by: by how much (if at all) to debounce/group the response chunks by. `None` means no debouncing.
            Debouncing is particularly important for long structured responses to reduce the overhead of
            performing validation as each token is received.

    Returns:
        An iterable of the structured response message and whether that is the last message.
    """
    return _utils.sync_async_iterator(self._streamed_run_result.stream_responses(debounce_by=debounce_by))

```

#### get_output

```python
get_output() -> OutputDataT

```

Stream the whole response, validate and return it.

Source code in `pydantic_ai_slim/pydantic_ai/result.py`

```python
def get_output(self) -> OutputDataT:
    """Stream the whole response, validate and return it."""
    return _utils.get_event_loop().run_until_complete(self._streamed_run_result.get_output())

```

#### response

```python
response: ModelResponse

```

Return the current state of the response.

#### usage

```python
usage() -> RunUsage

```

Return the usage of the whole run.

Note

This won't return the full usage until the stream is finished.

Source code in `pydantic_ai_slim/pydantic_ai/result.py`

```python
def usage(self) -> RunUsage:
    """Return the usage of the whole run.

    !!! note
        This won't return the full usage until the stream is finished.
    """
    return self._streamed_run_result.usage()

```

#### timestamp

```python
timestamp() -> datetime

```

Get the timestamp of the response.

Source code in `pydantic_ai_slim/pydantic_ai/result.py`

```python
def timestamp(self) -> datetime:
    """Get the timestamp of the response."""
    return self._streamed_run_result.timestamp()

```

#### run_id

```python
run_id: str

```

The unique identifier for the agent run.

#### validate_response_output

```python
validate_response_output(
    message: ModelResponse, *, allow_partial: bool = False
) -> OutputDataT

```

Validate a structured result message.

Source code in `pydantic_ai_slim/pydantic_ai/result.py`

```python
def validate_response_output(self, message: _messages.ModelResponse, *, allow_partial: bool = False) -> OutputDataT:
    """Validate a structured result message."""
    return _utils.get_event_loop().run_until_complete(
        self._streamed_run_result.validate_response_output(message, allow_partial=allow_partial)
    )

```

#### is_complete

```python
is_complete: bool

```

Whether the stream has all been received.

This is set to `True` when one of stream_output, stream_text, stream_responses or get_output completes.
