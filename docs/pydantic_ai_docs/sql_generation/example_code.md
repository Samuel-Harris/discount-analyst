## Example Code

[sql_gen.py](https://github.com/pydantic/pydantic-ai/blob/main/examples/pydantic_ai_examples/sql_gen.py)

```python
"""Example demonstrating how to use Pydantic AI to generate SQL queries based on user input.

Run postgres with:

    mkdir postgres-data
    docker run --rm -e POSTGRES_PASSWORD=postgres -p 54320:5432 postgres

Run with:

    uv run -m pydantic_ai_examples.sql_gen "show me logs from yesterday, with level 'error'"
"""

import asyncio
import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import date
from typing import Annotated, Any, TypeAlias

import asyncpg
import logfire
from annotated_types import MinLen
from devtools import debug
from pydantic import BaseModel, Field

from pydantic_ai import Agent, ModelRetry, RunContext, format_as_xml
