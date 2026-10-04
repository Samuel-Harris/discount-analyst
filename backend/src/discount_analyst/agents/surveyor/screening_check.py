"""Reject Surveyor metrics that were not copied from the screening tool."""

from __future__ import annotations

from collections.abc import Sequence
from typing import cast

from pydantic import ValidationError

from discount_analyst.agents.surveyor.schema import SurveyorCandidate
from discount_analyst.agents.tools.screening import (
    COMPUTE_SCREENING_METRICS_TOOL,
    ScreeningMetricsResult,
)
from discount_analyst.domain.screening.metrics import metrics_within_tolerance


class SurveyorScreeningMetricError(ValueError):
    """A non-null screening metric does not match the tool log."""


def assert_screening_metrics_match_tool_results(
    candidates: Sequence[SurveyorCandidate],
    messages: Sequence[object] | None,
) -> None:
    """Fail the stage when a non-null yield or CAGR was not copied from the tool.

    Null metrics are allowed with or without a tool call. The latest
    ``compute_screening_metrics`` return for each ticker wins.
    """
    latest = latest_screening_metrics_by_ticker(messages)
    for candidate in candidates:
        result = latest.get(candidate.ticker.casefold())
        _assert_metric(
            ticker=candidate.ticker,
            field_name="free_cash_flow_yield_pct",
            reported=candidate.key_metrics.free_cash_flow_yield_pct,
            computed=None if result is None else result.free_cash_flow_yield_pct,
        )
        _assert_metric(
            ticker=candidate.ticker,
            field_name="revenue_growth_3y_cagr_pct",
            reported=candidate.key_metrics.revenue_growth_3y_cagr_pct,
            computed=None if result is None else result.revenue_growth_3y_cagr_pct,
        )


def latest_screening_metrics_by_ticker(
    messages: Sequence[object] | None,
) -> dict[str, ScreeningMetricsResult]:
    """Last successful screening-tool return for each ticker, casefolded."""
    latest: dict[str, ScreeningMetricsResult] = {}
    if not messages:
        return latest
    for message in messages:
        for tool_name, content in _tool_returns(message):
            if tool_name != COMPUTE_SCREENING_METRICS_TOOL:
                continue
            parsed = _parse_result(content)
            if parsed is None:
                continue
            latest[parsed.ticker.casefold()] = parsed
    return latest


def _assert_metric(
    *,
    ticker: str,
    field_name: str,
    reported: float | None,
    computed: float | None,
) -> None:
    if metrics_within_tolerance(reported, computed):
        return
    if computed is None:
        msg = (
            f"{ticker} {field_name} is {reported} but there is no "
            f"{COMPUTE_SCREENING_METRICS_TOOL} result to copy."
        )
    else:
        msg = (
            f"{ticker} {field_name} is {reported} but the latest "
            f"{COMPUTE_SCREENING_METRICS_TOOL} result is {computed} "
            "(tolerance 0.1 percentage points)."
        )
    raise SurveyorScreeningMetricError(msg)


def _tool_returns(message: object) -> list[tuple[str | None, object]]:
    parts = _parts(message)
    found: list[tuple[str | None, object]] = []
    for part in parts:
        kind, tool_name, content = _part_fields(part)
        if kind in {"tool-return", "builtin-tool-return"}:
            found.append((tool_name, content))
    return found


def _parts(message: object) -> list[object]:
    if isinstance(message, dict):
        raw = cast(dict[str, object], message).get("parts", [])
    else:
        raw = getattr(message, "parts", [])
    if not isinstance(raw, list):
        return []
    return cast(list[object], raw)


def _part_fields(part: object) -> tuple[str | None, str | None, object]:
    if isinstance(part, dict):
        mapping = cast(dict[str, object], part)
        return (
            _optional_str(mapping.get("part_kind")),
            _optional_str(mapping.get("tool_name")),
            mapping.get("content"),
        )
    return (
        _optional_str(getattr(part, "part_kind", None)),
        _optional_str(getattr(part, "tool_name", None)),
        getattr(part, "content", None),
    )


def _parse_result(content: object) -> ScreeningMetricsResult | None:
    if isinstance(content, ScreeningMetricsResult):
        return content
    if isinstance(content, str):
        try:
            return ScreeningMetricsResult.model_validate_json(content)
        except ValidationError:
            return None
    if isinstance(content, dict):
        try:
            return ScreeningMetricsResult.model_validate(content)
        except ValidationError:
            return None
    return None


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)
