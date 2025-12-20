## Example Code

[Learn about Gateway](../../gateway) [flight_booking.py](https://github.com/pydantic/pydantic-ai/blob/main/examples/pydantic_ai_examples/flight_booking.py)

```python
"""Example of a multi-agent flow where one agent delegates work to another.

In this scenario, a group of agents work together to find flights for a user.
"""

import datetime
from dataclasses import dataclass
from typing import Literal

import logfire
from pydantic import BaseModel, Field
from rich.prompt import Prompt

from pydantic_ai import (
    Agent,
    ModelMessage,
    ModelRetry,
    RunContext,
    RunUsage,
    UsageLimits,
)
