"""Text-only local web fetch for providers that reject binary message parts."""

from __future__ import annotations

import asyncio
import io
import os
import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from markitdown import (
    FileConversionException,
    MarkItDown,
    StreamInfo,
    UnsupportedFormatException,
)
from pydantic_ai.common_tools.web_fetch import WebFetchLocalTool, WebFetchResult
from pydantic_ai.messages import BinaryContent
from pydantic_ai.tools import Tool

__all__ = ("create_text_only_web_fetch_tool",)

_EXCESSIVE_NEWLINES_RE = re.compile(r"\n{3,}")
_MARKITDOWN = MarkItDown(enable_plugins=False)


def _clean_whitespace(text: str) -> str:
    return _EXCESSIVE_NEWLINES_RE.sub("\n\n", text).strip()


def _truncate_content(content: str, *, max_content_length: int | None) -> str:
    if max_content_length is not None and len(content) > max_content_length:
        return content[:max_content_length] + "\n\n[Content truncated]"
    return content


def _unsupported_file_type_message(media_type: str) -> str:
    return (
        f"Unsupported file type: {media_type}. "
        "The file could not be converted to text. "
        "Try an HTML or JSON URL, or use another financial data tool."
    )


def _stream_info_for_binary(*, media_type: str, url: str) -> StreamInfo:
    parsed = urlparse(url)
    filename = os.path.basename(parsed.path) or None
    extension = os.path.splitext(filename)[1] if filename else None
    return StreamInfo(
        mimetype=media_type,
        url=url,
        filename=filename,
        extension=extension,
    )


def _binary_to_markdown(data: bytes, *, media_type: str, url: str) -> str:
    stream_info = _stream_info_for_binary(media_type=media_type, url=url)
    result = _MARKITDOWN.convert_stream(
        io.BytesIO(data),
        stream_info=stream_info,
    )
    return result.text_content


@dataclass
class TextOnlyWebFetchLocalTool(WebFetchLocalTool):
    """Fetches URLs and converts all responses to text for text-only model APIs."""

    async def __call__(self, url: str) -> WebFetchResult:
        result = await super().__call__(url)
        if not isinstance(result, BinaryContent):
            return result

        media_type = result.media_type
        try:
            content = await asyncio.to_thread(
                _binary_to_markdown,
                result.data,
                media_type=media_type,
                url=url,
            )
        except (UnsupportedFormatException, FileConversionException):
            return WebFetchResult(
                url=url,
                title="",
                content=_unsupported_file_type_message(media_type),
            )

        content = _clean_whitespace(content)
        if not content:
            return WebFetchResult(
                url=url,
                title="",
                content=_unsupported_file_type_message(media_type),
            )

        content = _truncate_content(
            content,
            max_content_length=self.max_content_length,
        )
        return WebFetchResult(url=url, title="", content=content)


def create_text_only_web_fetch_tool(
    *,
    max_content_length: int | None = 50_000,
    allow_local_urls: bool = False,
    timeout: int = 30,
    allowed_domains: list[str] | None = None,
    blocked_domains: list[str] | None = None,
    headers: dict[str, str] | None = None,
) -> Tool[Any]:
    """Create a web fetch tool that never returns binary content to the model."""
    return Tool[Any](
        TextOnlyWebFetchLocalTool(
            max_content_length=max_content_length,
            allow_local_urls=allow_local_urls,
            timeout=timeout,
            allowed_domains=allowed_domains,
            blocked_domains=blocked_domains,
            headers=headers,
        ).__call__,
        name="web_fetch",
        description=(
            "Fetches the content of a web page at the given URL and returns it as markdown."
        ),
    )
