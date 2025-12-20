### Exception Handling

The next example demonstrates the exception-handling capabilities of `FallbackModel`. If all models fail, a FallbackExceptionGroup is raised, which contains all the exceptions encountered during the `run` execution.

fallback_model_failure.py

```python
from pydantic_ai import Agent, ModelAPIError
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.fallback import FallbackModel
from pydantic_ai.models.openai import OpenAIChatModel

openai_model = OpenAIChatModel('gpt-5')
anthropic_model = AnthropicModel('claude-sonnet-4-5')
fallback_model = FallbackModel(openai_model, anthropic_model)

agent = Agent(fallback_model)
try:
    response = agent.run_sync('What is the capital of France?')
except* ModelAPIError as exc_group:
    for exc in exc_group.exceptions:
        print(exc)

```

Since [`except*`](https://docs.python.org/3/reference/compound_stmts.html#except-star) is only supported in Python 3.11+, we use the [`exceptiongroup`](https://github.com/agronholm/exceptiongroup) backport package for earlier Python versions:

fallback_model_failure.py

```python
from exceptiongroup import catch

from pydantic_ai import Agent, ModelAPIError
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.fallback import FallbackModel
from pydantic_ai.models.openai import OpenAIChatModel


def model_status_error_handler(exc_group: BaseExceptionGroup) -> None:
    for exc in exc_group.exceptions:
        print(exc)


openai_model = OpenAIChatModel('gpt-5')
anthropic_model = AnthropicModel('claude-sonnet-4-5')
fallback_model = FallbackModel(openai_model, anthropic_model)

agent = Agent(fallback_model)
with catch({ModelAPIError: model_status_error_handler}):
    response = agent.run_sync('What is the capital of France?')

```

By default, the `FallbackModel` only moves on to the next model if the current model raises a ModelAPIError, which includes ModelHTTPError. You can customize this behavior by passing a custom `fallback_on` argument to the `FallbackModel` constructor.

Note

Validation errors (from [structured output](../../output/#structured-output) or [tool parameters](../../tools/)) do **not** trigger fallback. These errors use the [retry mechanism](../../agents/#reflection-and-self-correction) instead, which re-prompts the same model to try again. This is intentional: validation errors stem from the non-deterministic nature of LLMs and may succeed on retry, whereas API errors (4xx/5xx) generally indicate issues that won't resolve by retrying the same request.
