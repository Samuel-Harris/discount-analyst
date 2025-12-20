### UsageLimits

Limits on model usage.

The request count is tracked by pydantic_ai, and the request limit is checked before each request to the model. Token counts are provided in responses from the model, and the token limits are checked after each response.

Each of the limits can be set to `None` to disable that limit.

Source code in `pydantic_ai_slim/pydantic_ai/usage.py`

```python
@dataclass(repr=False, kw_only=True)
class UsageLimits:
    """Limits on model usage.

    The request count is tracked by pydantic_ai, and the request limit is checked before each request to the model.
    Token counts are provided in responses from the model, and the token limits are checked after each response.

    Each of the limits can be set to `None` to disable that limit.
    """

    request_limit: int | None = 50
    """The maximum number of requests allowed to the model."""
    tool_calls_limit: int | None = None
    """The maximum number of successful tool calls allowed to be executed."""
    input_tokens_limit: int | None = None
    """The maximum number of input/prompt tokens allowed."""
    output_tokens_limit: int | None = None
    """The maximum number of output/response tokens allowed."""
    total_tokens_limit: int | None = None
    """The maximum number of tokens allowed in requests and responses combined."""
    count_tokens_before_request: bool = False
    """If True, perform a token counting pass before sending the request to the model,
    to enforce `request_tokens_limit` ahead of time. This may incur additional overhead
    (from calling the model's `count_tokens` API before making the actual request) and is disabled by default."""

    @property
    @deprecated('`request_tokens_limit` is deprecated, use `input_tokens_limit` instead')
    def request_tokens_limit(self) -> int | None:
        return self.input_tokens_limit

    @property
    @deprecated('`response_tokens_limit` is deprecated, use `output_tokens_limit` instead')
    def response_tokens_limit(self) -> int | None:
        return self.output_tokens_limit

    @overload
    def __init__(
        self,
        *,
        request_limit: int | None = 50,
        tool_calls_limit: int | None = None,
        input_tokens_limit: int | None = None,
        output_tokens_limit: int | None = None,
        total_tokens_limit: int | None = None,
        count_tokens_before_request: bool = False,
    ) -> None:
        self.request_limit = request_limit
        self.tool_calls_limit = tool_calls_limit
        self.input_tokens_limit = input_tokens_limit
        self.output_tokens_limit = output_tokens_limit
        self.total_tokens_limit = total_tokens_limit
        self.count_tokens_before_request = count_tokens_before_request

    @overload
    @deprecated(
        'Use `input_tokens_limit` instead of `request_tokens_limit` and `output_tokens_limit` and `total_tokens_limit`'
    )
    def __init__(
        self,
        *,
        request_limit: int | None = 50,
        tool_calls_limit: int | None = None,
        request_tokens_limit: int | None = None,
        response_tokens_limit: int | None = None,
        total_tokens_limit: int | None = None,
        count_tokens_before_request: bool = False,
    ) -> None:
        self.request_limit = request_limit
        self.tool_calls_limit = tool_calls_limit
        self.input_tokens_limit = request_tokens_limit
        self.output_tokens_limit = response_tokens_limit
        self.total_tokens_limit = total_tokens_limit
        self.count_tokens_before_request = count_tokens_before_request

    def __init__(
        self,
        *,
        request_limit: int | None = 50,
        tool_calls_limit: int | None = None,
        input_tokens_limit: int | None = None,
        output_tokens_limit: int | None = None,
        total_tokens_limit: int | None = None,
        count_tokens_before_request: bool = False,
        # deprecated:
        request_tokens_limit: int | None = None,
        response_tokens_limit: int | None = None,
    ):
        self.request_limit = request_limit
        self.tool_calls_limit = tool_calls_limit
        self.input_tokens_limit = input_tokens_limit or request_tokens_limit
        self.output_tokens_limit = output_tokens_limit or response_tokens_limit
        self.total_tokens_limit = total_tokens_limit
        self.count_tokens_before_request = count_tokens_before_request

    def has_token_limits(self) -> bool:
        """Returns `True` if this instance places any limits on token counts.

        If this returns `False`, the `check_tokens` method will never raise an error.

        This is useful because if we have token limits, we need to check them after receiving each streamed message.
        If there are no limits, we can skip that processing in the streaming response iterator.
        """
        return any(
            limit is not None for limit in (self.input_tokens_limit, self.output_tokens_limit, self.total_tokens_limit)
        )

    def check_before_request(self, usage: RunUsage) -> None:
        """Raises a `UsageLimitExceeded` exception if the next request would exceed any of the limits."""
        request_limit = self.request_limit
        if request_limit is not None and usage.requests >= request_limit:
            raise UsageLimitExceeded(f'The next request would exceed the request_limit of {request_limit}')

        input_tokens = usage.input_tokens
        if self.input_tokens_limit is not None and input_tokens > self.input_tokens_limit:
            raise UsageLimitExceeded(
                f'The next request would exceed the input_tokens_limit of {self.input_tokens_limit} ({input_tokens=})'
            )

        total_tokens = usage.total_tokens
        if self.total_tokens_limit is not None and total_tokens > self.total_tokens_limit:
            raise UsageLimitExceeded(  # pragma: lax no cover
                f'The next request would exceed the total_tokens_limit of {self.total_tokens_limit} ({total_tokens=})'
            )

    def check_tokens(self, usage: RunUsage) -> None:
        """Raises a `UsageLimitExceeded` exception if the usage exceeds any of the token limits."""
        input_tokens = usage.input_tokens
        if self.input_tokens_limit is not None and input_tokens > self.input_tokens_limit:
            raise UsageLimitExceeded(f'Exceeded the input_tokens_limit of {self.input_tokens_limit} ({input_tokens=})')

        output_tokens = usage.output_tokens
        if self.output_tokens_limit is not None and output_tokens > self.output_tokens_limit:
            raise UsageLimitExceeded(
                f'Exceeded the output_tokens_limit of {self.output_tokens_limit} ({output_tokens=})'
            )

        total_tokens = usage.total_tokens
        if self.total_tokens_limit is not None and total_tokens > self.total_tokens_limit:
            raise UsageLimitExceeded(f'Exceeded the total_tokens_limit of {self.total_tokens_limit} ({total_tokens=})')

    def check_before_tool_call(self, projected_usage: RunUsage) -> None:
        """Raises a `UsageLimitExceeded` exception if the next tool call(s) would exceed the tool call limit."""
        tool_calls_limit = self.tool_calls_limit
        tool_calls = projected_usage.tool_calls
        if tool_calls_limit is not None and tool_calls > tool_calls_limit:
            raise UsageLimitExceeded(
                f'The next tool call(s) would exceed the tool_calls_limit of {tool_calls_limit} ({tool_calls=}).'
            )

    __repr__ = _utils.dataclasses_no_defaults_repr

```

#### request_limit

```python
request_limit: int | None = request_limit

```

The maximum number of requests allowed to the model.

#### tool_calls_limit

```python
tool_calls_limit: int | None = tool_calls_limit

```

The maximum number of successful tool calls allowed to be executed.

#### input_tokens_limit

```python
input_tokens_limit: int | None = (
    input_tokens_limit or request_tokens_limit
)

```

The maximum number of input/prompt tokens allowed.

#### output_tokens_limit

```python
output_tokens_limit: int | None = (
    output_tokens_limit or response_tokens_limit
)

```

The maximum number of output/response tokens allowed.

#### total_tokens_limit

```python
total_tokens_limit: int | None = total_tokens_limit

```

The maximum number of tokens allowed in requests and responses combined.

#### count_tokens_before_request

```python
count_tokens_before_request: bool = (
    count_tokens_before_request
)

```

If True, perform a token counting pass before sending the request to the model, to enforce `request_tokens_limit` ahead of time. This may incur additional overhead (from calling the model's `count_tokens` API before making the actual request) and is disabled by default.

#### has_token_limits

```python
has_token_limits() -> bool

```

Returns `True` if this instance places any limits on token counts.

If this returns `False`, the `check_tokens` method will never raise an error.

This is useful because if we have token limits, we need to check them after receiving each streamed message. If there are no limits, we can skip that processing in the streaming response iterator.

Source code in `pydantic_ai_slim/pydantic_ai/usage.py`

```python
def has_token_limits(self) -> bool:
    """Returns `True` if this instance places any limits on token counts.

    If this returns `False`, the `check_tokens` method will never raise an error.

    This is useful because if we have token limits, we need to check them after receiving each streamed message.
    If there are no limits, we can skip that processing in the streaming response iterator.
    """
    return any(
        limit is not None for limit in (self.input_tokens_limit, self.output_tokens_limit, self.total_tokens_limit)
    )

```

#### check_before_request

```python
check_before_request(usage: RunUsage) -> None

```

Raises a `UsageLimitExceeded` exception if the next request would exceed any of the limits.

Source code in `pydantic_ai_slim/pydantic_ai/usage.py`

```python
def check_before_request(self, usage: RunUsage) -> None:
    """Raises a `UsageLimitExceeded` exception if the next request would exceed any of the limits."""
    request_limit = self.request_limit
    if request_limit is not None and usage.requests >= request_limit:
        raise UsageLimitExceeded(f'The next request would exceed the request_limit of {request_limit}')

    input_tokens = usage.input_tokens
    if self.input_tokens_limit is not None and input_tokens > self.input_tokens_limit:
        raise UsageLimitExceeded(
            f'The next request would exceed the input_tokens_limit of {self.input_tokens_limit} ({input_tokens=})'
        )

    total_tokens = usage.total_tokens
    if self.total_tokens_limit is not None and total_tokens > self.total_tokens_limit:
        raise UsageLimitExceeded(  # pragma: lax no cover
            f'The next request would exceed the total_tokens_limit of {self.total_tokens_limit} ({total_tokens=})'
        )

```

#### check_tokens

```python
check_tokens(usage: RunUsage) -> None

```

Raises a `UsageLimitExceeded` exception if the usage exceeds any of the token limits.

Source code in `pydantic_ai_slim/pydantic_ai/usage.py`

```python
def check_tokens(self, usage: RunUsage) -> None:
    """Raises a `UsageLimitExceeded` exception if the usage exceeds any of the token limits."""
    input_tokens = usage.input_tokens
    if self.input_tokens_limit is not None and input_tokens > self.input_tokens_limit:
        raise UsageLimitExceeded(f'Exceeded the input_tokens_limit of {self.input_tokens_limit} ({input_tokens=})')

    output_tokens = usage.output_tokens
    if self.output_tokens_limit is not None and output_tokens > self.output_tokens_limit:
        raise UsageLimitExceeded(
            f'Exceeded the output_tokens_limit of {self.output_tokens_limit} ({output_tokens=})'
        )

    total_tokens = usage.total_tokens
    if self.total_tokens_limit is not None and total_tokens > self.total_tokens_limit:
        raise UsageLimitExceeded(f'Exceeded the total_tokens_limit of {self.total_tokens_limit} ({total_tokens=})')

```

#### check_before_tool_call

```python
check_before_tool_call(projected_usage: RunUsage) -> None

```

Raises a `UsageLimitExceeded` exception if the next tool call(s) would exceed the tool call limit.

Source code in `pydantic_ai_slim/pydantic_ai/usage.py`

```python
def check_before_tool_call(self, projected_usage: RunUsage) -> None:
    """Raises a `UsageLimitExceeded` exception if the next tool call(s) would exceed the tool call limit."""
    tool_calls_limit = self.tool_calls_limit
    tool_calls = projected_usage.tool_calls
    if tool_calls_limit is not None and tool_calls > tool_calls_limit:
        raise UsageLimitExceeded(
            f'The next tool call(s) would exceed the tool_calls_limit of {tool_calls_limit} ({tool_calls=}).'
        )

```
