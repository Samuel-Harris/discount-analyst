"""Async FMP stable REST client for pipeline data-quality gates."""

from __future__ import annotations

from typing import Any, cast

import httpx
from httpx import HTTPStatusError
from pydantic import BaseModel, Field

from discount_analyst.http.retrying_client import create_rate_limit_client

FMP_STABLE_BASE_URL = "https://financialmodelingprep.com/stable"


class FmpAccessDeniedError(RuntimeError):
    """FMP returned HTTP 402 or 403 (tier / permission denied)."""

    def __init__(self, *, status_code: int, symbol_or_query: str) -> None:
        self.status_code = status_code
        self.symbol_or_query = symbol_or_query
        super().__init__(
            f"FMP access denied (HTTP {status_code}) for {symbol_or_query!r}"
        )


class FmpProfile(BaseModel):
    symbol: str
    company_name: str = Field(alias="companyName")
    exchange: str | None = None
    is_actively_trading: bool | None = Field(default=None, alias="isActivelyTrading")

    model_config = {"populate_by_name": True}


class FmpSearchResult(BaseModel):
    symbol: str
    name: str
    exchange: str | None = None


class FmpClient:
    """Thin httpx wrapper around FMP stable profile and search endpoints."""

    def __init__(
        self,
        api_key: str,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
        timeout_s: float = 30.0,
    ) -> None:
        self._api_key = api_key
        self._transport = transport
        self._timeout_s = timeout_s

    async def profile(self, symbol: str) -> list[FmpProfile]:
        payload = await self._get("profile", params={"symbol": symbol})
        return [FmpProfile.model_validate(row) for row in _as_dict_rows(payload)]

    async def search_symbol(self, query: str) -> list[FmpSearchResult]:
        payload = await self._get("search-symbol", params={"query": query})
        return [FmpSearchResult.model_validate(row) for row in _as_dict_rows(payload)]

    async def _get(self, path: str, *, params: dict[str, str]) -> Any:
        request_params = {**params, "apikey": self._api_key}
        async with self._client() as client:
            try:
                response = await client.get(
                    f"{FMP_STABLE_BASE_URL}/{path}",
                    params=request_params,
                )
            except HTTPStatusError as exc:
                self._raise_access_denied_if_plan_gated(exc, params=params, path=path)
                raise
        return self._response_payload(response, params=params, path=path)

    def _raise_access_denied_if_plan_gated(
        self,
        exc: HTTPStatusError,
        *,
        params: dict[str, str],
        path: str,
    ) -> None:
        if exc.response.status_code in (402, 403):
            raise self._access_denied_error(
                status_code=exc.response.status_code,
                params=params,
                path=path,
            ) from exc

    def _response_payload(
        self,
        response: httpx.Response,
        *,
        params: dict[str, str],
        path: str,
    ) -> Any:
        if response.status_code in (402, 403):
            raise self._access_denied_error(
                status_code=response.status_code,
                params=params,
                path=path,
            )
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _access_denied_error(
        *,
        status_code: int,
        params: dict[str, str],
        path: str,
    ) -> FmpAccessDeniedError:
        key = params.get("symbol") or params.get("query") or path
        return FmpAccessDeniedError(status_code=status_code, symbol_or_query=key)

    def _client(self) -> httpx.AsyncClient:
        if self._transport is not None:
            return httpx.AsyncClient(
                transport=self._transport,
                timeout=self._timeout_s,
            )
        return create_rate_limit_client(timeout=self._timeout_s)


def _as_dict_rows(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, list):
        return []
    rows: list[dict[str, Any]] = []
    payload_rows = cast(list[object], payload)
    for row in payload_rows:
        if isinstance(row, dict):
            rows.append(cast(dict[str, Any], row))
    return rows
