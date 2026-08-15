from __future__ import annotations

import math
import socket
from collections.abc import Callable
from datetime import UTC, date, datetime

import httpx
import pytest
from pydantic_ai import RunContext
from pydantic_ai.models.test import TestModel
from pydantic_ai.usage import RunUsage

from discount_analyst.agents.tools.market_data import frankfurter as frankfurter_module
from discount_analyst.agents.tools.market_data.frankfurter import (
    convert_currency,
    create_frankfurter_toolset,
)
from discount_analyst.agents.tools.terminal.infallible_toolset import InfallibleToolset


def _install_mock_client(
    monkeypatch: pytest.MonkeyPatch,
    handler: Callable[[httpx.Request], httpx.Response],
) -> list[httpx.Request]:
    requests: list[httpx.Request] = []

    def transport_handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        response = handler(request)
        if response.status_code >= 400:
            raise httpx.HTTPStatusError(
                f"{response.status_code} {response.reason_phrase}",
                request=request,
                response=response,
            )
        return response

    def fake_create_rate_limit_client(
        *, timeout: float | None = None
    ) -> httpx.AsyncClient:
        return httpx.AsyncClient(transport=httpx.MockTransport(transport_handler))

    monkeypatch.setattr(
        frankfurter_module, "create_rate_limit_client", fake_create_rate_limit_client
    )
    return requests


async def _call_convert_currency_tool(**tool_args: object) -> object:
    toolset = create_frankfurter_toolset()
    ctx = RunContext(deps=None, model=TestModel(), usage=RunUsage())
    tools = await toolset.get_tools(ctx)
    return await toolset.call_tool(
        "convert_currency", tool_args, ctx, tools["convert_currency"]
    )


async def test_convert_currency_multiplies_stubbed_rate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url).endswith("/v2/rate/EUR/USD")
        return httpx.Response(
            200,
            json={
                "date": "2026-08-15",
                "base": "EUR",
                "quote": "USD",
                "rate": 1.1,
            },
            request=request,
        )

    _install_mock_client(monkeypatch, handler)
    result = await convert_currency(10, "EUR", "USD")
    assert result.amount == 10
    assert result.from_currency == "EUR"
    assert result.to_currency == "USD"
    assert result.rate == 1.1
    assert result.rate_date == date(2026, 8, 15)
    assert result.converted_amount == 11.0


async def test_same_currency_skips_http(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError(f"unexpected HTTP call: {request.url}")

    requests = _install_mock_client(monkeypatch, handler)
    result = await convert_currency(25, "GBP", "GBP")
    assert requests == []
    assert result.rate == 1.0
    assert result.converted_amount == 25
    assert result.from_currency == "GBP"
    assert result.to_currency == "GBP"
    assert result.rate_date == datetime.now(UTC).date()


async def test_currency_codes_are_normalised(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url).endswith("/v2/rate/EUR/USD")
        return httpx.Response(
            200,
            json={
                "date": "2026-01-02",
                "base": "EUR",
                "quote": "USD",
                "rate": 2.0,
            },
            request=request,
        )

    _install_mock_client(monkeypatch, handler)
    result = await convert_currency(3, "eur", " usd ")
    assert result.from_currency == "EUR"
    assert result.to_currency == "USD"
    assert result.converted_amount == 6.0


@pytest.mark.parametrize("amount", [math.nan, math.inf, -math.inf])
async def test_non_finite_amount_raises(amount: float) -> None:
    with pytest.raises(ValueError, match="finite"):
        await convert_currency(amount, "EUR", "USD")


@pytest.mark.parametrize("amount", [math.nan, math.inf, -math.inf])
async def test_non_finite_amount_is_tool_error_string(amount: float) -> None:
    result = await _call_convert_currency_tool(
        amount=amount, from_currency="EUR", to_currency="USD"
    )
    assert isinstance(result, str)
    assert "convert_currency" in result
    assert "finite" in result.lower() or "failed" in result.lower()


async def test_unknown_currency_404_is_infallible_error_string(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text="Not Found", request=request)

    _install_mock_client(monkeypatch, handler)
    result = await _call_convert_currency_tool(
        amount=1, from_currency="EUR", to_currency="ZZZ"
    )
    assert isinstance(result, str)
    assert "404" in result
    assert "convert_currency" in result


def test_create_frankfurter_toolset_is_infallible() -> None:
    toolset = create_frankfurter_toolset()
    assert isinstance(toolset, InfallibleToolset)


@pytest.mark.network
async def test_live_eur_usd_smoke() -> None:
    try:
        result = await convert_currency(1, "EUR", "USD")
    except (httpx.ConnectError, httpx.TimeoutException, socket.gaierror) as exc:
        pytest.skip(f"Frankfurter unreachable: {exc}")
    assert result.from_currency == "EUR"
    assert result.to_currency == "USD"
    assert result.rate > 0
    assert result.converted_amount == result.amount * result.rate
