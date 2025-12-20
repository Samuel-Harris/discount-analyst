### Logfire with an alternative OTel backend

You can use the Logfire SDK completely freely and send the data to any OpenTelemetry backend.

Here's an example of configuring the Logfire library to send data to the excellent [otel-tui](https://github.com/ymtdzzz/otel-tui) â€” an open source terminal based OTel backend and viewer (no association with Pydantic Validation).

Run `otel-tui` with docker (see [the otel-tui readme](https://github.com/ymtdzzz/otel-tui) for more instructions):

Terminal

```text
docker run --rm -it -p 4318:4318 --name otel-tui ymtdzzz/otel-tui:latest

```

then run,

[Learn about Gateway](../gateway) otel_tui.py

```python
import os

import logfire

from pydantic_ai import Agent

os.environ['OTEL_EXPORTER_OTLP_ENDPOINT'] = 'http://localhost:4318'  # (1)!
logfire.configure(send_to_logfire=False)  # (2)!
logfire.instrument_pydantic_ai()
logfire.instrument_httpx(capture_all=True)

agent = Agent('gateway/openai:gpt-5')
result = agent.run_sync('What is the capital of France?')
print(result.output)
#> Paris

```

1. Set the `OTEL_EXPORTER_OTLP_ENDPOINT` environment variable to the URL of your OpenTelemetry backend. If you're using a backend that requires authentication, you may need to set [other environment variables](https://opentelemetry.io/docs/languages/sdk-configuration/otlp-exporter/). Of course, these can also be set outside the process, e.g. with `export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318`.
1. We configure Logfire to disable sending data to the Logfire OTel backend itself. If you removed `send_to_logfire=False`, data would be sent to both Logfire and your OpenTelemetry backend.

otel_tui.py

```python
import os

import logfire

from pydantic_ai import Agent

os.environ['OTEL_EXPORTER_OTLP_ENDPOINT'] = 'http://localhost:4318'  # (1)!
logfire.configure(send_to_logfire=False)  # (2)!
logfire.instrument_pydantic_ai()
logfire.instrument_httpx(capture_all=True)

agent = Agent('openai:gpt-5')
result = agent.run_sync('What is the capital of France?')
print(result.output)
#> Paris

```

1. Set the `OTEL_EXPORTER_OTLP_ENDPOINT` environment variable to the URL of your OpenTelemetry backend. If you're using a backend that requires authentication, you may need to set [other environment variables](https://opentelemetry.io/docs/languages/sdk-configuration/otlp-exporter/). Of course, these can also be set outside the process, e.g. with `export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318`.
1. We configure Logfire to disable sending data to the Logfire OTel backend itself. If you removed `send_to_logfire=False`, data would be sent to both Logfire and your OpenTelemetry backend.

Running the above code will send tracing data to `otel-tui`, which will display like this:

Running the [weather agent](../examples/weather-agent/) example connected to `otel-tui` shows how it can be used to visualise a more complex trace:

For more information on using the Logfire SDK to send data to alternative backends, see [the Logfire documentation](https://logfire.pydantic.dev/docs/how-to-guides/alternative-backends/).
