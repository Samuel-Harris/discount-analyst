from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from markitdown import FileConversionException, UnsupportedFormatException
from pydantic_ai.common_tools.web_fetch import WebFetchResult
from pydantic_ai.messages import BinaryContent
from pydantic_ai.tools import Tool

from discount_analyst.agents.tools.web_research import text_only_web_fetch as module
from discount_analyst.agents.tools.web_research.text_only_web_fetch import (
    TextOnlyWebFetchLocalTool,
    create_text_only_web_fetch_tool,
)

FIXTURE_DIR = Path(__file__).resolve().parents[2] / "fixtures" / "web_fetch"


@pytest.fixture
def text_only_tool() -> TextOnlyWebFetchLocalTool:
    return TextOnlyWebFetchLocalTool(
        max_content_length=50_000,
        allow_local_urls=False,
        timeout=30,
    )


def _raise_unsupported_format(*_args: object, **_kwargs: object) -> str:
    raise UnsupportedFormatException()


def _raise_file_conversion(*_args: object, **_kwargs: object) -> str:
    raise FileConversionException()


def _return_converted_text(converted_text: str):
    def _converter(*_args: object, **_kwargs: object) -> str:
        return converted_text

    return _converter


async def test_html_result_passes_through_unchanged(
    text_only_tool: TextOnlyWebFetchLocalTool,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = WebFetchResult(
        url="https://example.com", title="Example", content="# Hi"
    )
    monkeypatch.setattr(
        module.WebFetchLocalTool,
        "__call__",
        AsyncMock(return_value=expected),
    )

    result = await text_only_tool("https://example.com")

    assert result == expected


async def test_unsupported_binary_returns_error_message(
    text_only_tool: TextOnlyWebFetchLocalTool,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        module.WebFetchLocalTool,
        "__call__",
        AsyncMock(
            return_value=BinaryContent(
                data=b"\x00\x01",
                media_type="application/x-unknown",
            )
        ),
    )
    monkeypatch.setattr(
        module,
        "_binary_to_markdown",
        _raise_unsupported_format,
    )

    result = await text_only_tool("https://example.com/file.bin")

    assert result["url"] == "https://example.com/file.bin"
    assert "Unsupported file type: application/x-unknown" in result["content"]


async def test_conversion_failure_returns_error_message(
    text_only_tool: TextOnlyWebFetchLocalTool,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        module.WebFetchLocalTool,
        "__call__",
        AsyncMock(
            return_value=BinaryContent(data=b"broken", media_type="application/pdf")
        ),
    )
    monkeypatch.setattr(
        module,
        "_binary_to_markdown",
        _raise_file_conversion,
    )

    result = await text_only_tool("https://example.com/report.pdf")

    assert "Unsupported file type: application/pdf" in result["content"]


@pytest.mark.parametrize("converted_text", ["", "   \n\n   "])
async def test_empty_conversion_returns_unsupported_message(
    text_only_tool: TextOnlyWebFetchLocalTool,
    monkeypatch: pytest.MonkeyPatch,
    converted_text: str,
) -> None:
    monkeypatch.setattr(
        module.WebFetchLocalTool,
        "__call__",
        AsyncMock(
            return_value=BinaryContent(data=b"pdf", media_type="application/pdf")
        ),
    )
    monkeypatch.setattr(
        module,
        "_binary_to_markdown",
        _return_converted_text(converted_text),
    )

    result = await text_only_tool("https://example.com/report.pdf")

    assert "Unsupported file type: application/pdf" in result["content"]


async def test_binary_conversion_uses_asyncio_to_thread(
    text_only_tool: TextOnlyWebFetchLocalTool,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        module.WebFetchLocalTool,
        "__call__",
        AsyncMock(
            return_value=BinaryContent(data=b"pdf", media_type="application/pdf")
        ),
    )
    to_thread_calls: list[tuple[object, tuple[object, ...], dict[str, object]]] = []

    async def fake_to_thread(func: object, /, *args: object, **kwargs: object) -> str:
        to_thread_calls.append((func, args, kwargs))
        return "Converted markdown"

    monkeypatch.setattr(module.asyncio, "to_thread", fake_to_thread)

    result = await text_only_tool("https://example.com/report.pdf")

    assert to_thread_calls
    called_func = to_thread_calls[0][0]
    assert getattr(called_func, "__name__") == "_binary_to_markdown"
    assert result["content"] == "Converted markdown"


async def _fetch_binary_fixture(
    text_only_tool: TextOnlyWebFetchLocalTool,
    monkeypatch: pytest.MonkeyPatch,
    *,
    data: bytes,
    media_type: str,
    url: str,
) -> WebFetchResult:
    monkeypatch.setattr(
        module.WebFetchLocalTool,
        "__call__",
        AsyncMock(
            return_value=BinaryContent(data=data, media_type=media_type),
        ),
    )
    return await text_only_tool(url)


async def test_pdf_fixture_converts_to_expected_text(
    text_only_tool: TextOnlyWebFetchLocalTool,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pdf_bytes = (FIXTURE_DIR / "minimal_text.pdf").read_bytes()
    result = await _fetch_binary_fixture(
        text_only_tool,
        monkeypatch,
        data=pdf_bytes,
        media_type="application/octet-stream",
        url="https://example.com/reports/minimal_text.pdf",
    )
    assert "Discount Analyst PDF fixture" in result["content"]


async def test_docx_fixture_converts_to_expected_text(
    text_only_tool: TextOnlyWebFetchLocalTool,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    docx_bytes = (FIXTURE_DIR / "minimal_text.docx").read_bytes()
    result = await _fetch_binary_fixture(
        text_only_tool,
        monkeypatch,
        data=docx_bytes,
        media_type="application/octet-stream",
        url="https://example.com/reports/minimal_text.docx",
    )
    assert "Discount Analyst DOCX fixture" in result["content"]


def test_create_text_only_web_fetch_tool_returns_named_tool() -> None:
    tool = create_text_only_web_fetch_tool()
    assert isinstance(tool, Tool)
    assert tool.name == "web_fetch"
