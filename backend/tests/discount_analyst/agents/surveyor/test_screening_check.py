"""Surveyor post-check: non-null screening metrics must match the tool log."""

import math

import pytest

from discount_analyst.adapters.simulation.mock_outputs import mock_surveyor_candidate
from discount_analyst.agents.surveyor.schema import KeyMetrics
from discount_analyst.agents.surveyor.screening_check import (
    SurveyorScreeningMetricError,
    assert_screening_metrics_match_tool_results,
)
from discount_analyst.agents.tools.screening import (
    COMPUTE_SCREENING_METRICS_TOOL,
    ScreeningMetricsResult,
    compute_screening_metrics,
)


def _candidate(**metrics: float | None):
    candidate = mock_surveyor_candidate(ticker="ENQ.L")
    return candidate.model_copy(
        update={"key_metrics": KeyMetrics.model_validate(metrics)}
    )


def _tool_message(result: ScreeningMetricsResult) -> dict[str, object]:
    return {
        "kind": "request",
        "parts": [
            {
                "part_kind": "tool-return",
                "tool_name": COMPUTE_SCREENING_METRICS_TOOL,
                "tool_call_id": "call-1",
                "content": result.model_dump(mode="json"),
            }
        ],
    }


def test_null_metrics_do_not_require_a_tool_call() -> None:
    candidate = _candidate()
    assert_screening_metrics_match_tool_results([candidate], None)


def test_non_null_metric_without_a_tool_call_fails() -> None:
    candidate = _candidate(free_cash_flow_yield_pct=8.0)
    with pytest.raises(
        SurveyorScreeningMetricError, match="no compute_screening_metrics"
    ):
        assert_screening_metrics_match_tool_results([candidate], [])


def test_non_null_metric_must_match_the_latest_tool_result() -> None:
    first = ScreeningMetricsResult(
        ticker="enq.l",
        free_cash_flow=1.0,
        free_cash_flow_yield_pct=4.0,
        revenue_growth_3y_cagr_pct=None,
    )
    latest = ScreeningMetricsResult(
        ticker="ENQ.L",
        free_cash_flow=2.0,
        free_cash_flow_yield_pct=8.0,
        revenue_growth_3y_cagr_pct=11.0,
    )
    candidate = _candidate(
        free_cash_flow_yield_pct=8.05,
        revenue_growth_3y_cagr_pct=11.0,
    )

    assert_screening_metrics_match_tool_results(
        [candidate],
        [_tool_message(first), _tool_message(latest)],
    )


def test_mismatched_metric_fails() -> None:
    result = ScreeningMetricsResult(
        ticker="ENQ.L",
        free_cash_flow=2.0,
        free_cash_flow_yield_pct=8.0,
        revenue_growth_3y_cagr_pct=None,
    )
    candidate = _candidate(free_cash_flow_yield_pct=9.0)
    with pytest.raises(SurveyorScreeningMetricError, match="tolerance 0.1"):
        assert_screening_metrics_match_tool_results(
            [candidate], [_tool_message(result)]
        )


def test_compute_screening_metrics_nulls_cagr_without_four_years() -> None:
    result = compute_screening_metrics(
        ticker="ENQ.L",
        operating_cash_flow=100.0,
        capital_expenditure=-30.0,
        free_cash_flow_currency="GBP",
        market_cap=1000.0,
        market_cap_currency="GBP",
    )

    assert result.free_cash_flow is not None
    assert math.isclose(result.free_cash_flow, 70.0)
    assert result.free_cash_flow_yield_pct is not None
    assert math.isclose(result.free_cash_flow_yield_pct, 7.0)
    assert result.revenue_growth_3y_cagr_pct is None
