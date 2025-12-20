### OTel without Logfire

You can also emit OpenTelemetry data from Pydantic AI without using Logfire at all.

To do this, you'll need to install and configure the OpenTelemetry packages you need. To run the following examples, use

Terminal

```text
uv run \
  --with 'pydantic-ai-slim[openai]' \
  --with opentelemetry-sdk \
  --with opentelemetry-exporter-otlp \
  raw_otel.py

```

[Learn about Gateway](../gateway) raw_otel.py

```python
import os

from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import set_tracer_provider

from pydantic_ai import Agent

os.environ['OTEL_EXPORTER_OTLP_ENDPOINT'] = 'http://localhost:4318'
exporter = OTLPSpanExporter()
span_processor = BatchSpanProcessor(exporter)
tracer_provider = TracerProvider()
tracer_provider.add_span_processor(span_processor)

set_tracer_provider(tracer_provider)

Agent.instrument_all()
agent = Agent('gateway/openai:gpt-5')
result = agent.run_sync('What is the capital of France?')
print(result.output)
#> Paris

```

raw_otel.py

```python
import os

from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import set_tracer_provider

from pydantic_ai import Agent

os.environ['OTEL_EXPORTER_OTLP_ENDPOINT'] = 'http://localhost:4318'
exporter = OTLPSpanExporter()
span_processor = BatchSpanProcessor(exporter)
tracer_provider = TracerProvider()
tracer_provider.add_span_processor(span_processor)

set_tracer_provider(tracer_provider)

Agent.instrument_all()
agent = Agent('openai:gpt-5')
result = agent.run_sync('What is the capital of France?')
print(result.output)
#> Paris

```
