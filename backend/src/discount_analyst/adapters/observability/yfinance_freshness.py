"""Compare the installed yfinance version with the latest release on PyPI."""

from __future__ import annotations

from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version

import httpx
import logfire
from packaging.version import InvalidVersion, Version

PYPI_YFINANCE_JSON_URL = "https://pypi.org/pypi/yfinance/json"
_PYPI_TIMEOUT_SECONDS = 3.0


@dataclass(frozen=True, slots=True)
class YfinanceFreshness:
    installed_version: str
    latest_version: str | None
    is_outdated: bool


def evaluate_yfinance_freshness(
    *,
    installed_version: str,
    latest_version: str | None,
) -> YfinanceFreshness:
    is_outdated = False
    if latest_version is not None:
        try:
            is_outdated = Version(installed_version) < Version(latest_version)
        except InvalidVersion:
            is_outdated = False
    return YfinanceFreshness(
        installed_version=installed_version,
        latest_version=latest_version,
        is_outdated=is_outdated,
    )


def installed_yfinance_version() -> str:
    try:
        return version("yfinance")
    except PackageNotFoundError:
        return "unknown"


async def check_yfinance_freshness() -> YfinanceFreshness:
    installed = installed_yfinance_version()
    try:
        latest = await _latest_yfinance_version_from_pypi()
    except (httpx.HTTPError, ValueError) as error:
        logfire.warning(
            "Could not check PyPI for a newer yfinance release",
            installed_version=installed,
            error=str(error),
        )
        return evaluate_yfinance_freshness(
            installed_version=installed,
            latest_version=None,
        )

    freshness = evaluate_yfinance_freshness(
        installed_version=installed,
        latest_version=latest,
    )
    if freshness.is_outdated:
        logfire.warning(
            "Installed yfinance is behind the latest PyPI release",
            installed_version=freshness.installed_version,
            latest_version=freshness.latest_version,
        )
    else:
        logfire.info(
            "Installed yfinance matches or exceeds the latest PyPI release",
            installed_version=freshness.installed_version,
            latest_version=freshness.latest_version,
        )
    return freshness


async def _latest_yfinance_version_from_pypi() -> str:
    async with httpx.AsyncClient(timeout=_PYPI_TIMEOUT_SECONDS) as client:
        response = await client.get(PYPI_YFINANCE_JSON_URL)
        response.raise_for_status()
        payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError("PyPI yfinance JSON is not an object")
    info = payload.get("info")
    if not isinstance(info, dict):
        raise ValueError("PyPI yfinance JSON is missing an info object")
    latest = info.get("version")
    if not isinstance(latest, str) or not latest.strip():
        raise ValueError("PyPI yfinance JSON is missing info.version")
    return latest.strip()
