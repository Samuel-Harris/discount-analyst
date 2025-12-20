### RetryConfig

Bases: `TypedDict`

The configuration for tenacity-based retrying.

These are precisely the arguments to the tenacity `retry` decorator, and they are generally used internally by passing them to that decorator via `@retry(**config)` or similar.

All fields are optional, and if not provided, the default values from the `tenacity.retry` decorator will be used.

Source code in `pydantic_ai_slim/pydantic_ai/retries.py`

```python
class RetryConfig(TypedDict, total=False):
    """The configuration for tenacity-based retrying.

    These are precisely the arguments to the tenacity `retry` decorator, and they are generally
    used internally by passing them to that decorator via `@retry(**config)` or similar.

    All fields are optional, and if not provided, the default values from the `tenacity.retry` decorator will be used.
    """

    sleep: Callable[[int | float], None | Awaitable[None]]
    """A sleep strategy to use for sleeping between retries.

    Tenacity's default for this argument is `tenacity.nap.sleep`."""

    stop: StopBaseT
    """
    A stop strategy to determine when to stop retrying.

    Tenacity's default for this argument is `tenacity.stop.stop_never`."""

    wait: WaitBaseT
    """
    A wait strategy to determine how long to wait between retries.

    Tenacity's default for this argument is `tenacity.wait.wait_none`."""

    retry: SyncRetryBaseT | RetryBaseT
    """A retry strategy to determine which exceptions should trigger a retry.

    Tenacity's default for this argument is `tenacity.retry.retry_if_exception_type()`."""

    before: Callable[[RetryCallState], None | Awaitable[None]]
    """
    A callable that is called before each retry attempt.

    Tenacity's default for this argument is `tenacity.before.before_nothing`."""

    after: Callable[[RetryCallState], None | Awaitable[None]]
    """
    A callable that is called after each retry attempt.

    Tenacity's default for this argument is `tenacity.after.after_nothing`."""

    before_sleep: Callable[[RetryCallState], None | Awaitable[None]] | None
    """
    An optional callable that is called before sleeping between retries.

    Tenacity's default for this argument is `None`."""

    reraise: bool
    """Whether to reraise the last exception if the retry attempts are exhausted, or raise a RetryError instead.

    Tenacity's default for this argument is `False`."""

    retry_error_cls: type[RetryError]
    """The exception class to raise when the retry attempts are exhausted and `reraise` is False.

    Tenacity's default for this argument is `tenacity.RetryError`."""

    retry_error_callback: Callable[[RetryCallState], Any | Awaitable[Any]] | None
    """An optional callable that is called when the retry attempts are exhausted and `reraise` is False.

    Tenacity's default for this argument is `None`."""

```

#### sleep

```python
sleep: Callable[[int | float], None | Awaitable[None]]

```

A sleep strategy to use for sleeping between retries.

Tenacity's default for this argument is `tenacity.nap.sleep`.

#### stop

```python
stop: StopBaseT

```

A stop strategy to determine when to stop retrying.

Tenacity's default for this argument is `tenacity.stop.stop_never`.

#### wait

```python
wait: WaitBaseT

```

A wait strategy to determine how long to wait between retries.

Tenacity's default for this argument is `tenacity.wait.wait_none`.

#### retry

```python
retry: RetryBaseT | RetryBaseT

```

A retry strategy to determine which exceptions should trigger a retry.

Tenacity's default for this argument is `tenacity.retry.retry_if_exception_type()`.

#### before

```python
before: Callable[[RetryCallState], None | Awaitable[None]]

```

A callable that is called before each retry attempt.

Tenacity's default for this argument is `tenacity.before.before_nothing`.

#### after

```python
after: Callable[[RetryCallState], None | Awaitable[None]]

```

A callable that is called after each retry attempt.

Tenacity's default for this argument is `tenacity.after.after_nothing`.

#### before_sleep

```python
before_sleep: (
    Callable[[RetryCallState], None | Awaitable[None]]
    | None
)

```

An optional callable that is called before sleeping between retries.

Tenacity's default for this argument is `None`.

#### reraise

```python
reraise: bool

```

Whether to reraise the last exception if the retry attempts are exhausted, or raise a RetryError instead.

Tenacity's default for this argument is `False`.

#### retry_error_cls

```python
retry_error_cls: type[RetryError]

```

The exception class to raise when the retry attempts are exhausted and `reraise` is False.

Tenacity's default for this argument is `tenacity.RetryError`.

#### retry_error_callback

```python
retry_error_callback: (
    Callable[[RetryCallState], Any | Awaitable[Any]] | None
)

```

An optional callable that is called when the retry attempts are exhausted and `reraise` is False.

Tenacity's default for this argument is `None`.
