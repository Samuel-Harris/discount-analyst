### Configuring data format

Pydantic AI follows the [OpenTelemetry Semantic Conventions for Generative AI systems](https://opentelemetry.io/docs/specs/semconv/gen-ai/). Specifically, it follows version 1.37.0 of the conventions by default, with a few exceptions. Certain span and attribute names are not spec compliant by default for compatibility reasons, but can be made compliant by passing InstrumentationSettings(version=3) (the default is currently `version=2`). This will change the following:

- The span name `agent run` becomes `invoke_agent {gen_ai.agent.name}` (with the agent name filled in)
- The span name `running tool` becomes `execute_tool {gen_ai.tool.name}` (with the tool name filled in)
- The attribute name `tool_arguments` becomes `gen_ai.tool.call.arguments`
- The attribute name `tool_response` becomes `gen_ai.tool.call.result`

To use [OpenTelemetry semantic conventions version 1.36.0](https://github.com/open-telemetry/semantic-conventions/blob/v1.36.0/docs/gen-ai/README.md) or older, pass InstrumentationSettings(version=1). Moreover, those semantic conventions specify that messages should be captured as individual events (logs) that are children of the request span, whereas by default, Pydantic AI instead collects these events into a JSON array which is set as a single large attribute called `events` on the request span. To change this, use `event_mode='logs'`:

[Learn about Gateway](../gateway) instrumentation_settings_event_mode.py

```python
import logfire

from pydantic_ai import Agent

logfire.configure()
logfire.instrument_pydantic_ai(version=1, event_mode='logs')
agent = Agent('gateway/openai:gpt-5')
result = agent.run_sync('What is the capital of France?')
print(result.output)
#> The capital of France is Paris.

```

instrumentation_settings_event_mode.py

```python
import logfire

from pydantic_ai import Agent

logfire.configure()
logfire.instrument_pydantic_ai(version=1, event_mode='logs')
agent = Agent('openai:gpt-5')
result = agent.run_sync('What is the capital of France?')
print(result.output)
#> The capital of France is Paris.

```

This won't look as good in the Logfire UI, and will also be removed from Pydantic AI in a future release, but may be useful for backwards compatibility.

Note that the OpenTelemetry Semantic Conventions are still experimental and are likely to change.
