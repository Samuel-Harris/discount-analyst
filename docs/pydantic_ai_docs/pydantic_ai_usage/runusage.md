### RunUsage

Bases: `UsageBase`

LLM usage associated with an agent run.

Responsibility for calculating request usage is on the model; Pydantic AI simply sums the usage information across requests.

Source code in `pydantic_ai_slim/pydantic_ai/usage.py`

```python
@dataclass(repr=False, kw_only=True)
class RunUsage(UsageBase):
    """LLM usage associated with an agent run.

    Responsibility for calculating request usage is on the model; Pydantic AI simply sums the usage information across requests.
    """

    requests: int = 0
    """Number of requests made to the LLM API."""

    tool_calls: int = 0
    """Number of successful tool calls executed during the run."""

    input_tokens: int = 0
    """Total number of input/prompt tokens."""

    cache_write_tokens: int = 0
    """Total number of tokens written to the cache."""

    cache_read_tokens: int = 0
    """Total number of tokens read from the cache."""

    input_audio_tokens: int = 0
    """Total number of audio input tokens."""

    cache_audio_read_tokens: int = 0
    """Total number of audio tokens read from the cache."""

    output_tokens: int = 0
    """Total number of output/completion tokens."""

    details: dict[str, int] = dataclasses.field(default_factory=dict)
    """Any extra details returned by the model."""

    def incr(self, incr_usage: RunUsage | RequestUsage) -> None:
        """Increment the usage in place.

        Args:
            incr_usage: The usage to increment by.
        """
        if isinstance(incr_usage, RunUsage):
            self.requests += incr_usage.requests
            self.tool_calls += incr_usage.tool_calls
        return _incr_usage_tokens(self, incr_usage)

    def __add__(self, other: RunUsage | RequestUsage) -> RunUsage:
        """Add two RunUsages together.

        This is provided so it's trivial to sum usage information from multiple runs.
        """
        new_usage = copy(self)
        new_usage.incr(other)
        return new_usage

```

#### requests

```python
requests: int = 0

```

Number of requests made to the LLM API.

#### tool_calls

```python
tool_calls: int = 0

```

Number of successful tool calls executed during the run.

#### input_tokens

```python
input_tokens: int = 0

```

Total number of input/prompt tokens.

#### cache_write_tokens

```python
cache_write_tokens: int = 0

```

Total number of tokens written to the cache.

#### cache_read_tokens

```python
cache_read_tokens: int = 0

```

Total number of tokens read from the cache.

#### input_audio_tokens

```python
input_audio_tokens: int = 0

```

Total number of audio input tokens.

#### cache_audio_read_tokens

```python
cache_audio_read_tokens: int = 0

```

Total number of audio tokens read from the cache.

#### output_tokens

```python
output_tokens: int = 0

```

Total number of output/completion tokens.

#### details

```python
details: dict[str, int] = field(default_factory=dict)

```

Any extra details returned by the model.

#### incr

```python
incr(incr_usage: RunUsage | RequestUsage) -> None

```

Increment the usage in place.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `incr_usage` | `RunUsage | RequestUsage` | The usage to increment by. | _required_ |

Source code in `pydantic_ai_slim/pydantic_ai/usage.py`

```python
def incr(self, incr_usage: RunUsage | RequestUsage) -> None:
    """Increment the usage in place.

    Args:
        incr_usage: The usage to increment by.
    """
    if isinstance(incr_usage, RunUsage):
        self.requests += incr_usage.requests
        self.tool_calls += incr_usage.tool_calls
    return _incr_usage_tokens(self, incr_usage)

```

#### **add**

```python
__add__(other: RunUsage | RequestUsage) -> RunUsage

```

Add two RunUsages together.

This is provided so it's trivial to sum usage information from multiple runs.

Source code in `pydantic_ai_slim/pydantic_ai/usage.py`

```python
def __add__(self, other: RunUsage | RequestUsage) -> RunUsage:
    """Add two RunUsages together.

    This is provided so it's trivial to sum usage information from multiple runs.
    """
    new_usage = copy(self)
    new_usage.incr(other)
    return new_usage

```
