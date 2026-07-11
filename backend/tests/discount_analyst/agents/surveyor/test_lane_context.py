"""Tests for Surveyor lane context helpers."""

from discount_analyst.adapters.simulation.mock_outputs import mock_surveyor_candidate


def test_candidate_to_lane_context_uses_resolved_ticker_when_provided() -> None:
    candidate = mock_surveyor_candidate(
        ticker="ULT.L", company_name="Ultimate Products"
    )
    lane_context = candidate.to_lane_context(resolved_ticker="ULTP.L")

    assert lane_context.ticker == "ULTP.L"
    assert lane_context.company_name == candidate.company_name
