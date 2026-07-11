from __future__ import annotations

import asyncio
from collections.abc import Callable

import anyio.to_thread
import pytest
from pydantic_ai.tools import Tool

from discount_analyst.agents.tools.web_research import bounded_web_search as module
from discount_analyst.agents.tools.web_research.bounded_web_search import (
    BoundedDuckDuckGoSearchTool,
    create_bounded_duckduckgo_search_tool,
)


class FakeDuckDuckGoClient:
    def __init__(
        self,
        *,
        responses: list[list[dict[str, str]]] | None = None,
        errors: list[Exception] | None = None,
        on_call: Callable[[], None] | None = None,
    ) -> None:
        self.responses = responses or []
        self.errors = errors or []
        self.on_call = on_call
        self.calls = 0

    def text(
        self, query: str, *, max_results: int | None = None
    ) -> list[dict[str, str]]:
        self.calls += 1
        if self.on_call is not None:
            self.on_call()
        if self.errors:
            raise self.errors.pop(0)
        if self.responses:
            return self.responses.pop(0)
        return [
            {
                "title": f"Result for {query}",
                "href": "https://example.com",
                "body": f"max_results={max_results}",
            }
        ]


@pytest.fixture(autouse=True)
def reset_search_semaphore(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(module, "_DDGS_SEARCH_SEMAPHORE", asyncio.Semaphore(1))


def _bounded_tool(
    client: FakeDuckDuckGoClient,
    *,
    max_results: int | None = None,
    max_attempts: int = 3,
    base_delay_s: float = 1.0,
    max_delay_s: float = 8.0,
    jitter_s: float = 0.5,
) -> BoundedDuckDuckGoSearchTool:
    return BoundedDuckDuckGoSearchTool(
        client=client,  # type: ignore[arg-type]
        max_results=max_results,
        max_attempts=max_attempts,
        base_delay_s=base_delay_s,
        max_delay_s=max_delay_s,
        jitter_s=jitter_s,
    )


async def test_bounded_search_returns_validated_results() -> None:
    client = FakeDuckDuckGoClient(
        responses=[
            [
                {
                    "title": "Example",
                    "href": "https://example.com",
                    "body": "Search body",
                }
            ]
        ]
    )
    tool = _bounded_tool(client, max_results=5)

    results = await tool("example query")

    assert results == [
        {
            "title": "Example",
            "href": "https://example.com",
            "body": "Search body",
        }
    ]
    assert client.calls == 1


async def test_concurrent_searches_execute_sequentially(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    active_calls = 0
    max_active_calls = 0

    async def fake_run_sync(func: Callable[..., object], /, *args: object) -> object:
        nonlocal active_calls, max_active_calls
        active_calls += 1
        max_active_calls = max(max_active_calls, active_calls)
        await asyncio.sleep(0)
        result = func(*args)
        active_calls -= 1
        return result

    monkeypatch.setattr(anyio.to_thread, "run_sync", fake_run_sync)
    tool = _bounded_tool(FakeDuckDuckGoClient())

    await asyncio.gather(tool("first query"), tool("second query"))

    assert max_active_calls == 1


async def test_transient_failures_retry_then_succeed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sleeps: list[float] = []

    async def fake_sleep(delay: float) -> None:
        sleeps.append(delay)

    monkeypatch.setattr(module.asyncio, "sleep", fake_sleep)
    client = FakeDuckDuckGoClient(
        errors=[TimeoutError("timed out")],
        responses=[
            [
                {
                    "title": "Recovered",
                    "href": "https://example.com/recovered",
                    "body": "Recovered body",
                }
            ]
        ],
    )
    tool = _bounded_tool(
        client,
        max_attempts=2,
        base_delay_s=0.1,
        jitter_s=0,
    )

    results = await tool("retry query")

    assert results[0]["title"] == "Recovered"
    assert client.calls == 2
    assert sleeps == [0.1]


async def test_final_transient_failure_returns_unavailable_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_sleep(_delay: float) -> None:
        return None

    monkeypatch.setattr(module.asyncio, "sleep", fake_sleep)
    client = FakeDuckDuckGoClient(
        errors=[
            TimeoutError("timed out"),
            TimeoutError("timed out"),
        ]
    )
    tool = _bounded_tool(
        client,
        max_attempts=2,
        base_delay_s=0,
        jitter_s=0,
    )

    results = await tool("broken query")

    assert results == [
        {
            "title": "Search unavailable after retries",
            "href": "",
            "body": (
                "DuckDuckGo search was unavailable for query 'broken query' after "
                "bounded retries (timeout). Record this as a data gap and continue "
                "with other available sources."
            ),
        }
    ]


async def test_non_transient_failures_raise() -> None:
    client = FakeDuckDuckGoClient(errors=[ValueError("invalid response")])
    tool = _bounded_tool(client)

    with pytest.raises(ValueError, match="invalid response"):
        await tool("programmer error")


def test_create_bounded_duckduckgo_search_tool_returns_named_tool() -> None:
    tool = create_bounded_duckduckgo_search_tool(
        duckduckgo_client=FakeDuckDuckGoClient()  # type: ignore[arg-type]
    )

    assert isinstance(tool, Tool)
    assert tool.name == "duckduckgo_search"
