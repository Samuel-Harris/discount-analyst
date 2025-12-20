## Using Logfire

To use Logfire, you'll need a Logfire [account](https://logfire.pydantic.dev). The Logfire Python SDK is included with `pydantic-ai`:

```bash
pip install pydantic-ai

```

```bash
uv add pydantic-ai

```

Or if you're using the slim package, you can install it with the `logfire` optional group:

```bash
pip install "pydantic-ai-slim[logfire]"

```

```bash
uv add "pydantic-ai-slim[logfire]"

```

Then authenticate your local environment with Logfire:

```bash
 logfire auth

```

```bash
uv run logfire auth

```

And configure a project to send data to:

```bash
 logfire projects new

```

```bash
uv run logfire projects new

```

(Or use an existing project with `logfire projects use`)

This will write to a `.logfire` directory in the current working directory, which the Logfire SDK will use for configuration at run time.

With that, you can start using Logfire to instrument Pydantic AI code:

[Learn about Gateway](../gateway) instrument_pydantic_ai.py

```python
import logfire

from pydantic_ai import Agent

logfire.configure()  # (1)!
logfire.instrument_pydantic_ai()  # (2)!

agent = Agent('gateway/openai:gpt-5', instructions='Be concise, reply with one sentence.')
result = agent.run_sync('Where does "hello world" come from?')  # (3)!
print(result.output)
"""
The first known use of "hello, world" was in a 1974 textbook about the C programming language.
"""

```

1. logfire.configure() configures the SDK, by default it will find the write token from the `.logfire` directory, but you can also pass a token directly.
1. logfire.instrument_pydantic_ai() enables instrumentation of Pydantic AI.
1. Since we've enabled instrumentation, a trace will be generated for each run, with spans emitted for models calls and tool function execution

instrument_pydantic_ai.py

```python
import logfire

from pydantic_ai import Agent

logfire.configure()  # (1)!
logfire.instrument_pydantic_ai()  # (2)!

agent = Agent('openai:gpt-5', instructions='Be concise, reply with one sentence.')
result = agent.run_sync('Where does "hello world" come from?')  # (3)!
print(result.output)
"""
The first known use of "hello, world" was in a 1974 textbook about the C programming language.
"""

```

1. logfire.configure() configures the SDK, by default it will find the write token from the `.logfire` directory, but you can also pass a token directly.
1. logfire.instrument_pydantic_ai() enables instrumentation of Pydantic AI.
1. Since we've enabled instrumentation, a trace will be generated for each run, with spans emitted for models calls and tool function execution

_(This example is complete, it can be run "as is")_

Which will display in Logfire thus:

The [Logfire documentation](https://logfire.pydantic.dev/docs/) has more details on how to use Logfire, including how to instrument other libraries like [HTTPX](https://logfire.pydantic.dev/docs/integrations/http-clients/httpx/) and [FastAPI](https://logfire.pydantic.dev/docs/integrations/web-frameworks/fastapi/).

Since Logfire is built on [OpenTelemetry](https://opentelemetry.io/), you can use the Logfire Python SDK to send data to any OpenTelemetry collector, see [below](#using-opentelemetry).
