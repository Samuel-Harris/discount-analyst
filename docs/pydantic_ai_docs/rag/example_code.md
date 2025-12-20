## Example Code

[Learn about Gateway](../../gateway) [rag.py](https://github.com/pydantic/pydantic-ai/blob/main/examples/pydantic_ai_examples/rag.py)

```python
"""RAG example with pydantic-ai â€” using vector search to augment a chat agent.

Run pgvector with:

    mkdir postgres-data
    docker run --rm -e POSTGRES_PASSWORD=postgres \
        -p 54320:5432 \
        -v `pwd`/postgres-data:/var/lib/postgresql/data \
        pgvector/pgvector:pg17

Build the search DB with:

    uv run -m pydantic_ai_examples.rag build

Ask the agent a question with:

    uv run -m pydantic_ai_examples.rag search "How do I configure logfire to work with FastAPI?"
"""

from __future__ import annotations as _annotations

import asyncio
import re
import sys
import unicodedata
from contextlib import asynccontextmanager
from dataclasses import dataclass

import asyncpg
import httpx
import logfire
import pydantic_core
from anyio import create_task_group
from openai import AsyncOpenAI
from pydantic import TypeAdapter
from typing_extensions import AsyncGenerator

from pydantic_ai import Agent, RunContext
