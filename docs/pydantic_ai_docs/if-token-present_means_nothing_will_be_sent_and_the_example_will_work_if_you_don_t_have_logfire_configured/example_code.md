## Example Code

[Learn about Gateway](../../gateway) [weather_agent.py](https://github.com/pydantic/pydantic-ai/blob/main/examples/pydantic_ai_examples/weather_agent.py)

```python
"""Example of Pydantic AI with multiple tools which the LLM needs to call in turn to answer a question.

In this case the idea is a "weather" agent â€” the user can ask for the weather in multiple cities,
the agent will use the `get_lat_lng` tool to get the latitude and longitude of the locations, then use
the `get_weather` tool to get the weather.

Run with:

    uv run -m pydantic_ai_examples.weather_agent
"""

from __future__ import annotations as _annotations

import asyncio
from dataclasses import dataclass
from typing import Any

import logfire
from httpx import AsyncClient
from pydantic import BaseModel

from pydantic_ai import Agent, RunContext
