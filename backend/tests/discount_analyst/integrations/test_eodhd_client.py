"""Tests for the EODHD REST client."""

from __future__ import annotations

import httpx
import pytest

from discount_analyst.adapters.market_data.eodhd_client import EodhdClient


@pytest.mark.anyio
async def test_eodhd_real_time_happy_path() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "/real-time/ULTP.L" in str(request.url)
        return httpx.Response(200, json={"code": "ULTP.L", "close": 123.45})

    client = EodhdClient("test-key", transport=httpx.MockTransport(handler))
    quote = await client.real_time("ULTP.L")

    assert quote is not None
    assert quote.close == 123.45


@pytest.mark.anyio
async def test_eodhd_real_time_coerces_na_close_to_none() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "/real-time/BOWL.L" in str(request.url)
        return httpx.Response(200, json={"code": "BOWL.L", "close": "NA"})

    client = EodhdClient("test-key", transport=httpx.MockTransport(handler))
    quote = await client.real_time("BOWL.L")

    assert quote is not None
    assert quote.close is None


@pytest.mark.anyio
async def test_eodhd_real_time_parses_numeric_string_close() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        del request
        return httpx.Response(200, json={"code": "BOWL.L", "close": "278.5"})

    client = EodhdClient("test-key", transport=httpx.MockTransport(handler))
    quote = await client.real_time("BOWL.L")

    assert quote is not None
    assert quote.close == 278.5


@pytest.mark.anyio
async def test_eodhd_fundamentals_general_parses_is_delisted() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        del request
        return httpx.Response(
            200,
            json={"General": {"Code": "RNO.L", "IsDelisted": True}},
        )

    client = EodhdClient("test-key", transport=httpx.MockTransport(handler))
    general = await client.fundamentals_general("RNO.L")

    assert general is not None
    assert general.is_delisted is True
