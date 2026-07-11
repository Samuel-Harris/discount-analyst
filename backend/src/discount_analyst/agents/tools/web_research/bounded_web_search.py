"""Bounded local web search fallback for Pydantic AI web-search capabilities."""

from __future__ import annotations

import asyncio
import random
import time
from dataclasses import KW_ONLY, dataclass
from typing import Any

from ddgs.ddgs import DDGS
from pydantic_ai.common_tools.duckduckgo import DuckDuckGoResult, DuckDuckGoSearchTool
from pydantic_ai.tools import Tool

from discount_analyst.agents.runtime.ai_logging import AI_LOGFIRE

_DDGS_SEARCH_SEMAPHORE = asyncio.Semaphore(1)
_TRANSIENT_ERROR_MESSAGES = (
    "timed out",
    "timeout",
    "rate limit",
    "ratelimit",
    "too many requests",
    "429",
    "temporarily unavailable",
    "connection",
)
_TRANSIENT_ERROR_TYPES = (
    "Timeout",
    "TimeoutError",
    "ReadTimeout",
    "ConnectTimeout",
    "RateLimit",
    "Ratelimit",
    "HTTPError",
    "TransportError",
    "ConnectionError",
)


def _search_unavailable_result(
    *, query: str, failure_category: str
) -> list[DuckDuckGoResult]:
    return [
        {
            "title": "Search unavailable after retries",
            "href": "",
            "body": (
                f"DuckDuckGo search was unavailable for query {query!r} after "
                f"bounded retries ({failure_category}). Record this as a data gap "
                "and continue with other available sources."
            ),
        }
    ]


def _is_transient_search_error(error: Exception) -> bool:
    if isinstance(error, (TimeoutError, OSError, ConnectionError)):
        return True

    type_name = type(error).__name__
    if any(marker in type_name for marker in _TRANSIENT_ERROR_TYPES):
        return True

    message = str(error).casefold()
    return any(marker in message for marker in _TRANSIENT_ERROR_MESSAGES)


def _failure_category(error: Exception) -> str:
    message = str(error).casefold()
    type_name = type(error).__name__.casefold()

    if "429" in message or "rate" in message or "ratelimit" in type_name:
        return "rate_limit"
    if "timeout" in message or "timed out" in message or "timeout" in type_name:
        return "timeout"
    if "connection" in message or "connection" in type_name:
        return "network"
    return "transient"


@dataclass
class BoundedDuckDuckGoSearchTool(DuckDuckGoSearchTool):
    """DuckDuckGo search with global concurrency and retry bounds."""

    _: KW_ONLY
    max_attempts: int = 3
    base_delay_s: float = 1.0
    max_delay_s: float = 8.0
    jitter_s: float = 0.5

    async def __call__(self, query: str) -> list[DuckDuckGoResult]:
        """Search DuckDuckGo and return a fallback result if transient failures persist."""
        async with _DDGS_SEARCH_SEMAPHORE:
            return await self._search_with_retries(query)

    async def _search_with_retries(self, query: str) -> list[DuckDuckGoResult]:
        start_time = time.monotonic()
        last_error: Exception | None = None

        for attempt in range(1, self.max_attempts + 1):
            try:
                AI_LOGFIRE.info(
                    "DuckDuckGo search attempt started",
                    query=query,
                    attempt=attempt,
                    max_attempts=self.max_attempts,
                )
                results = await super().__call__(query)
                AI_LOGFIRE.info(
                    "DuckDuckGo search attempt succeeded",
                    query=query,
                    attempt=attempt,
                    elapsed_s=round(time.monotonic() - start_time, 3),
                    result_count=len(results),
                )
                return results
            except Exception as error:
                if not _is_transient_search_error(error):
                    raise

                last_error = error
                failure_category = _failure_category(error)
                AI_LOGFIRE.warning(
                    "DuckDuckGo search attempt failed",
                    query=query,
                    attempt=attempt,
                    max_attempts=self.max_attempts,
                    elapsed_s=round(time.monotonic() - start_time, 3),
                    failure_category=failure_category,
                    exception_type=type(error).__name__,
                )

                if attempt < self.max_attempts:
                    await asyncio.sleep(self._delay_for_attempt(attempt))

        assert last_error is not None
        failure_category = _failure_category(last_error)
        AI_LOGFIRE.warning(
            "DuckDuckGo search unavailable after retries",
            query=query,
            attempts=self.max_attempts,
            elapsed_s=round(time.monotonic() - start_time, 3),
            failure_category=failure_category,
            exception_type=type(last_error).__name__,
        )
        return _search_unavailable_result(
            query=query, failure_category=failure_category
        )

    def _delay_for_attempt(self, attempt: int) -> float:
        delay = min(self.max_delay_s, self.base_delay_s * (2 ** (attempt - 1)))
        if self.jitter_s <= 0:
            return delay
        return delay + random.uniform(0, self.jitter_s)


def create_bounded_duckduckgo_search_tool(
    *,
    duckduckgo_client: DDGS | None = None,
    max_results: int | None = None,
    max_attempts: int = 3,
    base_delay_s: float = 1.0,
    max_delay_s: float = 8.0,
    jitter_s: float = 0.5,
) -> Tool[Any]:
    """Create a bounded DuckDuckGo local search tool for Pydantic AI."""
    return Tool[Any](
        BoundedDuckDuckGoSearchTool(
            client=duckduckgo_client or DDGS(),
            max_results=max_results,
            max_attempts=max_attempts,
            base_delay_s=base_delay_s,
            max_delay_s=max_delay_s,
            jitter_s=jitter_s,
        ).__call__,
        name="duckduckgo_search",
        description="Searches DuckDuckGo for the given query and returns the results.",
    )
