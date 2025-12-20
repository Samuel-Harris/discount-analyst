### wait_retry_after

The `wait_retry_after` function is a smart wait strategy that automatically respects HTTP `Retry-After` headers:

wait_strategy_example.py

```python
from tenacity import wait_exponential

from pydantic_ai.retries import wait_retry_after
