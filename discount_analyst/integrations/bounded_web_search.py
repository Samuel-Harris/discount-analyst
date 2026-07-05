"""Bounded local web search fallback for Pydantic AI web-search capabilities."""

from __future__ import annotations

import asyncio
import functools
import random
import time
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import KW_ONLY, dataclass
from typing import Any, Literal, Protocol, cast

import anyio.to_thread
from pydantic import TypeAdapter
from pydantic_ai.capabilities import WebSearch
from pydantic_ai.capabilities.abstract import AbstractCapability
from pydantic_ai.capabilities.web_search import WebSearchLocalStrategy
from pydantic_ai.native_tools import WebSearchTool, WebSearchUserLocation
from pydantic_ai.tools import AgentDepsT, AgentNativeTool, RunContext, Tool
from pydantic_ai.toolsets import AgentToolset
from typing_extensions import TypedDict

from discount_analyst.agents.common.ai_logging import AI_LOGFIRE

try:
    from ddgs.ddgs import DDGS as _DDGS
except ImportError as _import_error:
    raise ImportError(
        "Please install `ddgs` to use the bounded DuckDuckGo search tool."
    ) from _import_error


class DuckDuckGoClient(Protocol):
    def text(self, query: str, *, max_results: int | None = None) -> object: ...


class DuckDuckGoResult(TypedDict):
    """A DuckDuckGo search result."""

    title: str
    href: str
    body: str


_DUCKDUCKGO_RESULT_ADAPTER = TypeAdapter(list[DuckDuckGoResult])
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
_DDGS_CLIENT_CLASS = cast("type[DuckDuckGoClient]", _DDGS)


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
class BoundedDuckDuckGoSearchTool:
    """DuckDuckGo search with global concurrency and retry bounds."""

    client: DuckDuckGoClient
    _: KW_ONLY
    max_results: int | None = None
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
                results = await self._search_once(query)
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

    async def _search_once(self, query: str) -> list[DuckDuckGoResult]:
        search = functools.partial(self.client.text, max_results=self.max_results)
        results = await anyio.to_thread.run_sync(search, query)
        return _DUCKDUCKGO_RESULT_ADAPTER.validate_python(results)

    def _delay_for_attempt(self, attempt: int) -> float:
        delay = min(self.max_delay_s, self.base_delay_s * (2 ** (attempt - 1)))
        if self.jitter_s <= 0:
            return delay
        return delay + random.uniform(0, self.jitter_s)


def create_bounded_duckduckgo_search_tool(
    *,
    duckduckgo_client: DuckDuckGoClient | None = None,
    max_results: int | None = None,
    max_attempts: int = 3,
    base_delay_s: float = 1.0,
    max_delay_s: float = 8.0,
    jitter_s: float = 0.5,
) -> Tool[Any]:
    """Create a bounded DuckDuckGo local search tool for Pydantic AI."""
    return Tool[Any](
        BoundedDuckDuckGoSearchTool(
            client=duckduckgo_client or _DDGS_CLIENT_CLASS(),
            max_results=max_results,
            max_attempts=max_attempts,
            base_delay_s=base_delay_s,
            max_delay_s=max_delay_s,
            jitter_s=jitter_s,
        ).__call__,
        name="duckduckgo_search",
        description="Searches DuckDuckGo for the given query and returns the results.",
    )


@dataclass(init=False)
class BoundedWebSearch(AbstractCapability[AgentDepsT]):
    """Pydantic AI WebSearch configured with a bounded DuckDuckGo local fallback."""

    web_search: WebSearch[AgentDepsT]

    def __init__(
        self,
        *,
        native: WebSearchTool
        | Callable[
            [RunContext[AgentDepsT]],
            Awaitable[WebSearchTool | None] | WebSearchTool | None,
        ]
        | bool = True,
        local: WebSearchLocalStrategy
        | Tool[AgentDepsT]
        | Callable[..., Any]
        | bool
        | None = None,
        search_context_size: Literal["low", "medium", "high"] | None = None,
        user_location: WebSearchUserLocation | None = None,
        blocked_domains: list[str] | None = None,
        allowed_domains: list[str] | None = None,
        max_uses: int | None = None,
        id: str | None = None,
        defer_loading: bool = False,
        description: str | None = None,
    ) -> None:
        self.id = id
        self.description = description
        self.defer_loading = defer_loading
        self.web_search = WebSearch(
            native=native,
            local=self._local_tool(local),
            search_context_size=search_context_size,
            user_location=user_location,
            blocked_domains=blocked_domains,
            allowed_domains=allowed_domains,
            max_uses=max_uses,
            id=id,
            defer_loading=defer_loading,
            description=description,
        )

    def get_native_tools(self) -> Sequence[AgentNativeTool[AgentDepsT]]:
        return self.web_search.get_native_tools()

    def get_toolset(self) -> AgentToolset[AgentDepsT] | None:
        return self.web_search.get_toolset()

    @staticmethod
    def _local_tool(
        local: WebSearchLocalStrategy
        | Tool[AgentDepsT]
        | Callable[..., Any]
        | bool
        | None,
    ) -> WebSearchLocalStrategy | Tool[AgentDepsT] | Callable[..., Any] | bool | None:
        if local is None or local is True or local == "duckduckgo":
            return create_bounded_duckduckgo_search_tool()
        return local
