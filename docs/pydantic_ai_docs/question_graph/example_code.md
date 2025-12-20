## Example Code

[Learn about Gateway](../../gateway) [question_graph.py](https://github.com/pydantic/pydantic-ai/blob/main/examples/pydantic_ai_examples/question_graph.py)

```python
"""Example of a graph for asking and evaluating questions.

Run with:

    uv run -m pydantic_ai_examples.question_graph
"""

from __future__ import annotations as _annotations

from dataclasses import dataclass, field
from pathlib import Path

import logfire
from groq import BaseModel

from pydantic_ai import Agent, ModelMessage, format_as_xml
from pydantic_graph import (
    BaseNode,
    End,
    Graph,
    GraphRunContext,
)
from pydantic_graph.persistence.file import FileStatePersistence
