from pathlib import Path
from uuid import uuid4

from httpx import AsyncClient, Response

from discount_analyst.agents.tools.http.retrying_client import create_rate_limit_client
from discount_analyst.agents.tools.regulatory_data.errors import (
    SecUserAgentMissingError,
)
from discount_analyst.config.settings import settings as app_settings

METADATA_TIMEOUT_SECONDS = 30.0
BULK_DOWNLOAD_TIMEOUT_SECONDS = 600.0
_STREAM_CHUNK_BYTES = 1024 * 64


def create_metadata_client() -> AsyncClient:
    """Retrying client for small official metadata and API responses."""
    return create_rate_limit_client(timeout=METADATA_TIMEOUT_SECONDS)


def create_bulk_client() -> AsyncClient:
    """Retrying client for streamed archive downloads that must not load into RAM."""
    return create_rate_limit_client(timeout=BULK_DOWNLOAD_TIMEOUT_SECONDS)


def resolved_sec_user_agent() -> str:
    user_agent = app_settings.sec_user_agent.strip()
    if not user_agent:
        raise SecUserAgentMissingError()
    return user_agent


def sec_request_headers() -> dict[str, str]:
    return {
        "User-Agent": resolved_sec_user_agent(),
        "Accept-Encoding": "gzip, deflate",
    }


async def stream_response_to_path(response: Response, dest: Path) -> None:
    """Write an already-opened streaming response to ``dest`` without buffering it."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(f".{dest.name}.{uuid4().hex}.tmp")
    try:
        with tmp.open("wb") as handle:
            async for chunk in response.aiter_bytes(_STREAM_CHUNK_BYTES):
                handle.write(chunk)
        tmp.replace(dest)
    finally:
        tmp.unlink(missing_ok=True)


async def stream_url_to_path(
    client: AsyncClient,
    url: str,
    dest: Path,
    *,
    headers: dict[str, str] | None = None,
) -> None:
    async with client.stream("GET", url, headers=headers) as response:
        response.raise_for_status()
        await stream_response_to_path(response, dest)
