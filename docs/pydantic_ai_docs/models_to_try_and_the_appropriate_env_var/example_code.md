## Example Code

[Learn about Gateway](../../gateway) [stream_whales.py](https://github.com/pydantic/pydantic-ai/blob/main/examples/pydantic_ai_examples/stream_whales.py)

```python
"""Information about whales â€” an example of streamed structured response validation.

This script streams structured responses from GPT-4 about whales, validates the data
and displays it as a dynamic table using Rich as the data is received.

Run with:

    uv run -m pydantic_ai_examples.stream_whales
"""

from typing import Annotated

import logfire
from pydantic import Field
from rich.console import Console
from rich.live import Live
from rich.table import Table
from typing_extensions import NotRequired, TypedDict

from pydantic_ai import Agent
