## Example Code

[stream_markdown.py](https://github.com/pydantic/pydantic-ai/blob/main/examples/pydantic_ai_examples/stream_markdown.py)

```python
"""This example shows how to stream markdown from an agent, using the `rich` library to display the markdown.

Run with:

    uv run -m pydantic_ai_examples.stream_markdown
"""

import asyncio
import os

import logfire
from rich.console import Console, ConsoleOptions, RenderResult
from rich.live import Live
from rich.markdown import CodeBlock, Markdown
from rich.syntax import Syntax
from rich.text import Text

from pydantic_ai import Agent
from pydantic_ai.models import KnownModelName
