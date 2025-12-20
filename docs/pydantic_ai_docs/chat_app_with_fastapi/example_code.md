## Example Code

Python code that runs the chat app:

[Learn about Gateway](../../gateway) [chat_app.py](https://github.com/pydantic/pydantic-ai/blob/main/examples/pydantic_ai_examples/chat_app.py)

```python
"""Simple chat app example build with FastAPI.

Run with:

    uv run -m pydantic_ai_examples.chat_app
"""

from __future__ import annotations as _annotations

import asyncio
import json
import sqlite3
from collections.abc import AsyncIterator, Callable
from concurrent.futures.thread import ThreadPoolExecutor
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import partial
from pathlib import Path
from typing import Annotated, Any, Literal, TypeVar

import fastapi
import logfire
from fastapi import Depends, Request
from fastapi.responses import FileResponse, Response, StreamingResponse
from typing_extensions import LiteralString, ParamSpec, TypedDict

from pydantic_ai import (
    Agent,
    ModelMessage,
    ModelMessagesTypeAdapter,
    ModelRequest,
    ModelResponse,
    TextPart,
    UnexpectedModelBehavior,
    UserPromptPart,
)
