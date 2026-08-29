"""Compare the installed yfinance version with the latest release on PyPI."""

from __future__ import annotations

from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from typing import Any, cast

import httpx
import logfire

PYPI_YFINANCE_JSON_URL = "https://pypi.org/pypi/yfinance/json"
_PYPI_TIMEOUT_SECONDS = 3.0


@dataclass(frozen=True, slots=True)
class YfinanceFreshness:
    installed_version: str
    latest_version: str | None
    is_outdated: bool


def version_tuple(value: str) -> tuple[int, ...]:
    """Numeric prefix of a PEP 440 version, e.g. ``1.7.0rc1`` → ``(1, 7, 0)``."""
    numbers: list[int] = []
    for part in value.strip().split("."):
        digits = ""
        for character in part:
            if character.isdigit():
                digits += character
            else:
                break
        if not digits:
            break
        numbers.append(int(digits))
    return tuple(numbers)


def evaluate_yfinance_freshness(
    *,
    installed_version: str,
    latest_version: str | None,
) -> YfinanceFreshness:
    installed_numbers = version_tuple(installed_version)
    latest_numbers = version_tuple(latest_version) if latest_version else ()
    is_outdated = bool(
        latest_version is not None
        and installed_numbers
        and latest_numbers
        and installed_numbers < latest_numbers
    )
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
    except Exception as error:
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
        payload = cast(dict[str, Any], response.json())
    info = payload.get("info")
    if not isinstance(info, dict):
        raise ValueError("PyPI yfinance JSON is missing an info object")
    latest = info.get("version")
    if not isinstance(latest, str) or not latest.strip():
        raise ValueError("PyPI yfinance JSON is missing info.version")
    return latest.strip()
