### Additional Configuration

#### Usage Limits

Pydantic AI offers a UsageLimits structure to help you limit your usage (tokens, requests, and tool calls) on model runs.

You can apply these settings by passing the `usage_limits` argument to the `run{_sync,_stream}` functions.

Consider the following example, where we limit the number of response tokens:

[Learn about Gateway](../gateway)

```python
from pydantic_ai import Agent, UsageLimitExceeded, UsageLimits

agent = Agent('gateway/anthropic:claude-sonnet-4-5')

result_sync = agent.run_sync(
    'What is the capital of Italy? Answer with just the city.',
    usage_limits=UsageLimits(response_tokens_limit=10),
)
print(result_sync.output)
#> Rome
print(result_sync.usage())
#> RunUsage(input_tokens=62, output_tokens=1, requests=1)

try:
    result_sync = agent.run_sync(
        'What is the capital of Italy? Answer with a paragraph.',
        usage_limits=UsageLimits(response_tokens_limit=10),
    )
except UsageLimitExceeded as e:
    print(e)
    #> Exceeded the output_tokens_limit of 10 (output_tokens=32)

```

```python
from pydantic_ai import Agent, UsageLimitExceeded, UsageLimits

agent = Agent('anthropic:claude-sonnet-4-5')

result_sync = agent.run_sync(
    'What is the capital of Italy? Answer with just the city.',
    usage_limits=UsageLimits(response_tokens_limit=10),
)
print(result_sync.output)
#> Rome
print(result_sync.usage())
#> RunUsage(input_tokens=62, output_tokens=1, requests=1)

try:
    result_sync = agent.run_sync(
        'What is the capital of Italy? Answer with a paragraph.',
        usage_limits=UsageLimits(response_tokens_limit=10),
    )
except UsageLimitExceeded as e:
    print(e)
    #> Exceeded the output_tokens_limit of 10 (output_tokens=32)

```

Restricting the number of requests can be useful in preventing infinite loops or excessive tool calling:

[Learn about Gateway](../gateway)

```python
from typing_extensions import TypedDict

from pydantic_ai import Agent, ModelRetry, UsageLimitExceeded, UsageLimits


class NeverOutputType(TypedDict):
    """
    Never ever coerce data to this type.
    """

    never_use_this: str


agent = Agent(
    'gateway/anthropic:claude-sonnet-4-5',
    retries=3,
    output_type=NeverOutputType,
    system_prompt='Any time you get a response, call the `infinite_retry_tool` to produce another response.',
)


@agent.tool_plain(retries=5)  # (1)!
def infinite_retry_tool() -> int:
    raise ModelRetry('Please try again.')


try:
    result_sync = agent.run_sync(
        'Begin infinite retry loop!', usage_limits=UsageLimits(request_limit=3)  # (2)!
    )
except UsageLimitExceeded as e:
    print(e)
    #> The next request would exceed the request_limit of 3

```

1. This tool has the ability to retry 5 times before erroring, simulating a tool that might get stuck in a loop.
1. This run will error after 3 requests, preventing the infinite tool calling.

```python
from typing_extensions import TypedDict

from pydantic_ai import Agent, ModelRetry, UsageLimitExceeded, UsageLimits


class NeverOutputType(TypedDict):
    """
    Never ever coerce data to this type.
    """

    never_use_this: str


agent = Agent(
    'anthropic:claude-sonnet-4-5',
    retries=3,
    output_type=NeverOutputType,
    system_prompt='Any time you get a response, call the `infinite_retry_tool` to produce another response.',
)


@agent.tool_plain(retries=5)  # (1)!
def infinite_retry_tool() -> int:
    raise ModelRetry('Please try again.')


try:
    result_sync = agent.run_sync(
        'Begin infinite retry loop!', usage_limits=UsageLimits(request_limit=3)  # (2)!
    )
except UsageLimitExceeded as e:
    print(e)
    #> The next request would exceed the request_limit of 3

```

1. This tool has the ability to retry 5 times before erroring, simulating a tool that might get stuck in a loop.
1. This run will error after 3 requests, preventing the infinite tool calling.

##### Capping tool calls

If you need a limit on the number of successful tool invocations within a single run, use `tool_calls_limit`:

[Learn about Gateway](../gateway)

```python
from pydantic_ai import Agent
from pydantic_ai.exceptions import UsageLimitExceeded
from pydantic_ai.usage import UsageLimits

agent = Agent('gateway/anthropic:claude-sonnet-4-5')

@agent.tool_plain
def do_work() -> str:
    return 'ok'

try:
    # Allow at most one executed tool call in this run
    agent.run_sync('Please call the tool twice', usage_limits=UsageLimits(tool_calls_limit=1))
except UsageLimitExceeded as e:
    print(e)
    #> The next tool call(s) would exceed the tool_calls_limit of 1 (tool_calls=2).

```

```python
from pydantic_ai import Agent
from pydantic_ai.exceptions import UsageLimitExceeded
from pydantic_ai.usage import UsageLimits

agent = Agent('anthropic:claude-sonnet-4-5')

@agent.tool_plain
def do_work() -> str:
    return 'ok'

try:
    # Allow at most one executed tool call in this run
    agent.run_sync('Please call the tool twice', usage_limits=UsageLimits(tool_calls_limit=1))
except UsageLimitExceeded as e:
    print(e)
    #> The next tool call(s) would exceed the tool_calls_limit of 1 (tool_calls=2).

```

Note

- Usage limits are especially relevant if you've registered many tools. Use `request_limit` to bound the number of model turns, and `tool_calls_limit` to cap the number of successful tool executions within a run.
- The `tool_calls_limit` is checked before executing tool calls. If the model returns parallel tool calls that would exceed the limit, no tools will be executed.

#### Model (Run) Settings

Pydantic AI offers a settings.ModelSettings structure to help you fine tune your requests. This structure allows you to configure common parameters that influence the model's behavior, such as `temperature`, `max_tokens`, `timeout`, and more.

There are three ways to apply these settings, with a clear precedence order:

1. **Model-level defaults** - Set when creating a model instance via the `settings` parameter. These serve as the base defaults for that model.
1. **Agent-level defaults** - Set during Agent initialization via the `model_settings` argument. These are merged with model defaults, with agent settings taking precedence.
1. **Run-time overrides** - Passed to `run{_sync,_stream}` functions via the `model_settings` argument. These have the highest priority and are merged with the combined agent and model defaults.

For example, if you'd like to set the `temperature` setting to `0.0` to ensure less random behavior, you can do the following:

```python
from pydantic_ai import Agent, ModelSettings
from pydantic_ai.models.openai import OpenAIChatModel
