### StreamedResponseSync

Synchronous wrapper to async streaming responses by running the async producer in a background thread and providing a synchronous iterator.

This class must be used as a context manager with the `with` statement.

Source code in `pydantic_ai_slim/pydantic_ai/direct.py`

```python
@dataclass
class StreamedResponseSync:
    """Synchronous wrapper to async streaming responses by running the async producer in a background thread and providing a synchronous iterator.

    This class must be used as a context manager with the `with` statement.
    """

    _async_stream_cm: AbstractAsyncContextManager[StreamedResponse]
    _queue: queue.Queue[messages.ModelResponseStreamEvent | Exception | None] = field(
        default_factory=queue.Queue, init=False
    )
    _thread: threading.Thread | None = field(default=None, init=False)
    _stream_response: StreamedResponse | None = field(default=None, init=False)
    _exception: Exception | None = field(default=None, init=False)
    _context_entered: bool = field(default=False, init=False)
    _stream_ready: threading.Event = field(default_factory=threading.Event, init=False)

    def __enter__(self) -> StreamedResponseSync:
        self._context_entered = True
        self._start_producer()
        return self

    def __exit__(
        self,
        _exc_type: type[BaseException] | None,
        _exc_val: BaseException | None,
        _exc_tb: TracebackType | None,
    ) -> None:
        self._cleanup()

    def __iter__(self) -> Iterator[messages.ModelResponseStreamEvent]:
        """Stream the response as an iterable of [`ModelResponseStreamEvent`][pydantic_ai.messages.ModelResponseStreamEvent]s."""
        self._check_context_manager_usage()

        while True:
            item = self._queue.get()
            if item is None:  # End of stream
                break
            elif isinstance(item, Exception):
                raise item
            else:
                yield item

    def __repr__(self) -> str:
        if self._stream_response:
            return repr(self._stream_response)
        else:
            return f'{self.__class__.__name__}(context_entered={self._context_entered})'

    __str__ = __repr__

    def _check_context_manager_usage(self) -> None:
        if not self._context_entered:
            raise RuntimeError(
                'StreamedResponseSync must be used as a context manager. '
                'Use: `with model_request_stream_sync(...) as stream:`'
            )

    def _ensure_stream_ready(self) -> StreamedResponse:
        self._check_context_manager_usage()

        if self._stream_response is None:
            # Wait for the background thread to signal that the stream is ready
            if not self._stream_ready.wait(timeout=STREAM_INITIALIZATION_TIMEOUT):
                raise RuntimeError('Stream failed to initialize within timeout')

            if self._stream_response is None:  # pragma: no cover
                raise RuntimeError('Stream failed to initialize')

        return self._stream_response

    def _start_producer(self):
        self._thread = threading.Thread(target=self._async_producer, daemon=True)
        self._thread.start()

    def _async_producer(self):
        async def _consume_async_stream():
            try:
                async with self._async_stream_cm as stream:
                    self._stream_response = stream
                    # Signal that the stream is ready
                    self._stream_ready.set()
                    async for event in stream:
                        self._queue.put(event)
            except Exception as e:
                # Signal ready even on error so waiting threads don't hang
                self._stream_ready.set()
                self._queue.put(e)
            finally:
                self._queue.put(None)  # Signal end

        _get_event_loop().run_until_complete(_consume_async_stream())

    def _cleanup(self):
        if self._thread and self._thread.is_alive():
            self._thread.join()

    # TODO (v2): Drop in favor of `response` property
    def get(self) -> messages.ModelResponse:
        """Build a ModelResponse from the data received from the stream so far."""
        return self._ensure_stream_ready().get()

    @property
    def response(self) -> messages.ModelResponse:
        """Get the current state of the response."""
        return self.get()

    # TODO (v2): Make this a property
    def usage(self) -> RequestUsage:
        """Get the usage of the response so far."""
        return self._ensure_stream_ready().usage()

    @property
    def model_name(self) -> str:
        """Get the model name of the response."""
        return self._ensure_stream_ready().model_name

    @property
    def timestamp(self) -> datetime:
        """Get the timestamp of the response."""
        return self._ensure_stream_ready().timestamp

```

#### **iter**

```python
__iter__() -> Iterator[ModelResponseStreamEvent]

```

Stream the response as an iterable of ModelResponseStreamEvents.

Source code in `pydantic_ai_slim/pydantic_ai/direct.py`

```python
def __iter__(self) -> Iterator[messages.ModelResponseStreamEvent]:
    """Stream the response as an iterable of [`ModelResponseStreamEvent`][pydantic_ai.messages.ModelResponseStreamEvent]s."""
    self._check_context_manager_usage()

    while True:
        item = self._queue.get()
        if item is None:  # End of stream
            break
        elif isinstance(item, Exception):
            raise item
        else:
            yield item

```

#### get

```python
get() -> ModelResponse

```

Build a ModelResponse from the data received from the stream so far.

Source code in `pydantic_ai_slim/pydantic_ai/direct.py`

```python
def get(self) -> messages.ModelResponse:
    """Build a ModelResponse from the data received from the stream so far."""
    return self._ensure_stream_ready().get()

```

#### response

```python
response: ModelResponse

```

Get the current state of the response.

#### usage

```python
usage() -> RequestUsage

```

Get the usage of the response so far.

Source code in `pydantic_ai_slim/pydantic_ai/direct.py`

```python
def usage(self) -> RequestUsage:
    """Get the usage of the response so far."""
    return self._ensure_stream_ready().usage()

```

#### model_name

```python
model_name: str

```

Get the model name of the response.

#### timestamp

```python
timestamp: datetime

```

Get the timestamp of the response.
