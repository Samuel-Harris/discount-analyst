### Monitoring HTTP Requests

As per Hamel Husain's influential 2024 blog post ["Fuck You, Show Me The Prompt."](https://hamel.dev/blog/posts/prompt/) (bear with the capitalization, the point is valid), it's often useful to be able to view the raw HTTP requests and responses made to model providers.

To observe raw HTTP requests made to model providers, you can use Logfire's [HTTPX instrumentation](https://logfire.pydantic.dev/docs/integrations/http-clients/httpx/) since all provider SDKs (except for [Bedrock](../models/bedrock/)) use the [HTTPX](https://www.python-httpx.org/) library internally:

[Learn about Gateway](../gateway) with_logfire_instrument_httpx.py

```python
import logfire

from pydantic_ai import Agent

logfire.configure()
logfire.instrument_pydantic_ai()
logfire.instrument_httpx(capture_all=True)  # (1)!

agent = Agent('gateway/openai:gpt-5')
result = agent.run_sync('What is the capital of France?')
print(result.output)
#> The capital of France is Paris.

```

1. See the logfire.instrument_httpx docs more details, `capture_all=True` means both headers and body are captured for both the request and response.

with_logfire_instrument_httpx.py

```python
import logfire

from pydantic_ai import Agent

logfire.configure()
logfire.instrument_pydantic_ai()
logfire.instrument_httpx(capture_all=True)  # (1)!

agent = Agent('openai:gpt-5')
result = agent.run_sync('What is the capital of France?')
print(result.output)
#> The capital of France is Paris.

```

1. See the logfire.instrument_httpx docs more details, `capture_all=True` means both headers and body are captured for both the request and response.
