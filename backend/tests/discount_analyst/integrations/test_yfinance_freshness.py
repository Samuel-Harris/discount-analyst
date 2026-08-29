"""Installed yfinance vs latest PyPI release."""

from __future__ import annotations

from typing import Any

import httpx
import pytest

from discount_analyst.adapters.market_data.yfinance_freshness import (
    PYPI_YFINANCE_JSON_URL,
    check_yfinance_freshness,
    evaluate_yfinance_freshness,
    version_tuple,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("1.7.0", (1, 7, 0)),
        ("0.2.66", (0, 2, 66)),
        ("1.7.0rc1", (1, 7, 0)),
        ("", ()),
    ],
)
def test_version_tuple(value: str, expected: tuple[int, ...]) -> None:
    assert version_tuple(value) == expected


@pytest.mark.parametrize(
    ("installed", "latest", "outdated"),
    [
        ("1.7.0", "1.7.0", False),
        ("1.7.0", "1.8.0", True),
        ("0.2.66", "1.7.0", True),
        ("1.8.0", "1.7.0", False),
        ("1.7.0", None, False),
    ],
)
def test_evaluate_yfinance_freshness(
    installed: str, latest: str | None, outdated: bool
) -> None:
    result = evaluate_yfinance_freshness(
        installed_version=installed,
        latest_version=latest,
    )
    assert result.installed_version == installed
    assert result.latest_version == latest
    assert result.is_outdated is outdated


async def test_check_yfinance_freshness_marks_older_install_outdated(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "discount_analyst.adapters.market_data.yfinance_freshness.installed_yfinance_version",
        lambda: "1.6.0",
    )

    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == PYPI_YFINANCE_JSON_URL
        return httpx.Response(200, json={"info": {"version": "1.7.0"}})

    original_client = httpx.AsyncClient

    def factory(**kwargs: Any) -> httpx.AsyncClient:
        kwargs["transport"] = httpx.MockTransport(handler)
        return original_client(**kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", factory)

    freshness = await check_yfinance_freshness()
    assert freshness.installed_version == "1.6.0"
    assert freshness.latest_version == "1.7.0"
    assert freshness.is_outdated is True


async def test_check_yfinance_freshness_does_not_warn_when_pypi_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "discount_analyst.adapters.market_data.yfinance_freshness.installed_yfinance_version",
        lambda: "1.7.0",
    )

    def handler(request: httpx.Request) -> httpx.Response:
        del request
        return httpx.Response(503, text="unavailable")

    original_client = httpx.AsyncClient

    def factory(**kwargs: Any) -> httpx.AsyncClient:
        kwargs["transport"] = httpx.MockTransport(handler)
        return original_client(**kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", factory)

    freshness = await check_yfinance_freshness()
    assert freshness.installed_version == "1.7.0"
    assert freshness.latest_version is None
    assert freshness.is_outdated is False
