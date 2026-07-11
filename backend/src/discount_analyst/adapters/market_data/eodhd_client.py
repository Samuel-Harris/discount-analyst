"""Async EODHD REST client for UK listing-status fallback when FMP denies access."""

from __future__ import annotations

from typing import Any, cast

import httpx
from pydantic import BaseModel, Field

from discount_analyst.agents.tools.http.retrying_client import create_rate_limit_client

EODHD_API_BASE_URL = "https://eodhd.com/api"


class EodhdGeneralInfo(BaseModel):
    code: str | None = None
    is_delisted: bool | None = Field(default=None, alias="IsDelisted")

    model_config = {"populate_by_name": True}


class EodhdRealTimeQuote(BaseModel):
    code: str | None = None
    close: float | None = None


class EodhdClient:
    """Minimal EODHD client for gate-time listing probes on ``.L`` symbols."""

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

    async def real_time(self, symbol: str) -> EodhdRealTimeQuote | None:
        payload = await self._get(f"real-time/{symbol}", params={"fmt": "json"})
        if not isinstance(payload, dict):
            return None
        return EodhdRealTimeQuote.model_validate(payload)

    async def fundamentals_general(self, symbol: str) -> EodhdGeneralInfo | None:
        payload = await self._get(f"fundamentals/{symbol}", params={"fmt": "json"})
        if not isinstance(payload, dict):
            return None
        payload_dict = cast(dict[str, Any], payload)
        general = payload_dict.get("General")
        if not isinstance(general, dict):
            return None
        return EodhdGeneralInfo.model_validate(cast(dict[str, Any], general))

    async def _get(self, path: str, *, params: dict[str, str]) -> Any:
        request_params = {**params, "api_token": self._api_key}
        async with self._client() as client:
            response = await client.get(
                f"{EODHD_API_BASE_URL}/{path}",
                params=request_params,
            )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()

    def _client(self) -> httpx.AsyncClient:
        if self._transport is not None:
            return httpx.AsyncClient(
                transport=self._transport,
                timeout=self._timeout_s,
            )
        return create_rate_limit_client(timeout=self._timeout_s)
