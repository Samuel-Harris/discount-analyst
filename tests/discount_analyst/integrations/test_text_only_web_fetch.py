from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from markitdown import FileConversionException, UnsupportedFormatException
from pydantic_ai.common_tools.web_fetch import WebFetchResult
from pydantic_ai.messages import BinaryContent
from pydantic_ai.tools import Tool

from discount_analyst.integrations import text_only_web_fetch as module
from discount_analyst.integrations.text_only_web_fetch import (
    TextOnlyWebFetchLocalTool,
    _binary_to_markdown,
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
        lambda *_args, **_kwargs: (_ for _ in ()).throw(UnsupportedFormatException()),
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
        lambda *_args, **_kwargs: (_ for _ in ()).throw(FileConversionException()),
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
        lambda *_args, **_kwargs: converted_text,
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
    assert to_thread_calls[0][0] is module._binary_to_markdown
    assert result["content"] == "Converted markdown"


def test_pdf_fixture_converts_to_expected_text() -> None:
    pdf_bytes = (FIXTURE_DIR / "minimal_text.pdf").read_bytes()
    content = _binary_to_markdown(
        pdf_bytes,
        media_type="application/octet-stream",
        url="https://example.com/reports/minimal_text.pdf",
    )
    assert "Discount Analyst PDF fixture" in content


def test_docx_fixture_converts_to_expected_text() -> None:
    docx_bytes = (FIXTURE_DIR / "minimal_text.docx").read_bytes()
    content = _binary_to_markdown(
        docx_bytes,
        media_type="application/octet-stream",
        url="https://example.com/reports/minimal_text.docx",
    )
    assert "Discount Analyst DOCX fixture" in content


def test_mislabelled_pdf_uses_url_extension() -> None:
    pdf_bytes = (FIXTURE_DIR / "minimal_text.pdf").read_bytes()
    content = _binary_to_markdown(
        pdf_bytes,
        media_type="application/octet-stream",
        url="https://example.com/reports/minimal_text.pdf",
    )
    assert "Discount Analyst PDF fixture" in content


def test_create_text_only_web_fetch_tool_returns_named_tool() -> None:
    tool = create_text_only_web_fetch_tool()
    assert isinstance(tool, Tool)
    assert tool.name == "web_fetch"
