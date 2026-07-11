"""Tests for the FMP stable REST client."""

from __future__ import annotations

import httpx
import pytest
from httpx import HTTPStatusError

from discount_analyst.adapters.market_data.fmp_client import (
    FmpAccessDeniedError,
    FmpClient,
)


class _HttpStatusErrorClient:
    def __init__(self, error: HTTPStatusError) -> None:
        self._error = error

    async def __aenter__(self) -> _HttpStatusErrorClient:
        return self

    async def __aexit__(self, *_args: object) -> None:
        return None

    async def get(self, *_args: object, **_kwargs: object) -> httpx.Response:
        raise self._error


@pytest.mark.anyio
async def test_fmp_profile_happy_path() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/profile")
        return httpx.Response(
            200,
            json=[
                {
                    "symbol": "ULTP.L",
                    "companyName": "Ultimate Products plc",
                    "exchange": "LSE",
                    "isActivelyTrading": True,
                }
            ],
        )

    client = FmpClient("test-key", transport=httpx.MockTransport(handler))
    profiles = await client.profile("ULTP.L")

    assert len(profiles) == 1
    assert profiles[0].symbol == "ULTP.L"
    assert profiles[0].company_name == "Ultimate Products plc"
    assert profiles[0].is_actively_trading is True


@pytest.mark.anyio
async def test_fmp_search_symbol_happy_path() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/search-symbol")
        return httpx.Response(
            200,
            json=[
                {
                    "symbol": "ULTP.L",
                    "name": "Ultimate Products plc",
                    "exchange": "LSE",
                }
            ],
        )

    client = FmpClient("test-key", transport=httpx.MockTransport(handler))
    results = await client.search_symbol("Ultimate Products")

    assert len(results) == 1
    assert results[0].symbol == "ULTP.L"


@pytest.mark.anyio
async def test_fmp_profile_raises_on_402() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        del request
        return httpx.Response(402, json={"error": "premium"})

    client = FmpClient("test-key", transport=httpx.MockTransport(handler))

    with pytest.raises(FmpAccessDeniedError) as exc_info:
        await client.profile("POLN.L")

    assert exc_info.value.status_code == 402


@pytest.mark.anyio
async def test_fmp_profile_maps_transport_http_status_error_to_access_denied(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = httpx.Request("GET", "https://financialmodelingprep.com/stable/profile")
    response = httpx.Response(402, request=request, json={"error": "premium"})
    error = HTTPStatusError("402", request=request, response=response)
    client = FmpClient("test-key")
    monkeypatch.setattr(client, "_client", lambda: _HttpStatusErrorClient(error))

    with pytest.raises(FmpAccessDeniedError) as exc_info:
        await client.profile("AOUT")

    assert exc_info.value.status_code == 402
    assert exc_info.value.symbol_or_query == "AOUT"
