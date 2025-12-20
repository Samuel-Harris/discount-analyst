## OpenTelemetry or Logfire Instrumentation

As with agents, you can enable OpenTelemetry/Logfire instrumentation with just a few extra lines

direct_instrumented.py

```python
import logfire

from pydantic_ai import ModelRequest
from pydantic_ai.direct import model_request_sync

logfire.configure()
logfire.instrument_pydantic_ai()
