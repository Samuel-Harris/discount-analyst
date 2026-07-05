"""Tests for pre-Researcher candidate gates."""

from __future__ import annotations

import pytest

from backend.dev.mock_outputs import mock_key_metrics, mock_surveyor_candidate
from backend.settings.testing import dashboard_settings_for_tests
from discount_analyst.agents.surveyor.schema import (
    Exchange,
    SurveyorCandidate,
)
from discount_analyst.integrations.eodhd_client import (
    EodhdGeneralInfo,
    EodhdRealTimeQuote,
)
from discount_analyst.integrations.fmp_client import (
    FmpProfile,
    FmpQuoteShort,
    FmpSearchResult,
)
from discount_analyst.pipeline.candidate_gates import (
    RejectedCandidateGate,
    company_name_similarity,
    validate_candidate,
)


def _candidate(
    *,
    ticker: str,
    company_name: str,
    exchange: Exchange = Exchange.LSE,
) -> SurveyorCandidate:
    return SurveyorCandidate(
        ticker=ticker,
        company_name=company_name,
        exchange=exchange,
        currency=mock_surveyor_candidate(ticker=ticker).currency,
        market_cap_local=100_000_000,
        market_cap_display="£100M",
        sector="Industrials",
        industry="Building Products",
        analyst_coverage_count=2,
        key_metrics=mock_key_metrics(),
        rationale="Screening rationale with £220M cap mention.",
        red_flags="None identified",
        data_gaps="None",
    )


class _RecordingFmpClient:
    def __init__(
        self,
        *,
        profile_rows: list[dict[str, object]],
        search_rows: list[dict[str, object]] | None = None,
    ) -> None:
        self._profile_rows = profile_rows
        self._search_rows = search_rows or []

    async def profile(self, symbol: str) -> list[FmpProfile]:
        del symbol
        return [FmpProfile.model_validate(row) for row in self._profile_rows]

    async def search_symbol(self, query: str) -> list[FmpSearchResult]:
        del query
        return [FmpSearchResult.model_validate(row) for row in self._search_rows]

    async def quote_short(self, symbol: str) -> list[FmpQuoteShort]:
        del symbol
        return [FmpQuoteShort(symbol="ULTP.L", price=10.0)]


class _DelistedEodhdClient:
    async def real_time(self, symbol: str) -> EodhdRealTimeQuote | None:
        del symbol
        return None

    async def fundamentals_general(self, symbol: str) -> EodhdGeneralInfo:
        del symbol
        return EodhdGeneralInfo(code="RNO.L", IsDelisted=True)


@pytest.mark.anyio
async def test_validate_candidate_resolves_ult_to_ultp() -> None:
    candidate = _candidate(ticker="ULT.L", company_name="Ultimate Products plc")
    fmp = _RecordingFmpClient(
        profile_rows=[
            {
                "symbol": "ULT.L",
                "companyName": "Unrelated plc",
                "exchange": "LSE",
                "isActivelyTrading": True,
            }
        ],
        search_rows=[
            {
                "symbol": "ULTP.L",
                "name": "Ultimate Products plc",
                "exchange": "LSE",
            }
        ],
    )
    settings = dashboard_settings_for_tests()

    result = await validate_candidate(
        candidate,
        settings=settings,
        fmp_client=fmp,  # type: ignore[arg-type]
    )

    assert result.gate_status == "passed"
    assert result.resolved_ticker == "ULTP.L"
    assert result.lane_context is not None
    assert result.lane_context.ticker == "ULTP.L"
    assert "market_cap_local" not in result.lane_context.model_dump()


@pytest.mark.anyio
async def test_validate_candidate_rejects_delisted_rno() -> None:
    candidate = _candidate(ticker="RNO.L", company_name="Renold plc")
    fmp = _RecordingFmpClient(
        profile_rows=[
            {
                "symbol": "RNO.L",
                "companyName": "Renold plc",
                "exchange": "LSE",
                "isActivelyTrading": False,
            }
        ],
    )
    settings = dashboard_settings_for_tests()

    result = await validate_candidate(
        candidate,
        settings=settings,
        fmp_client=fmp,  # type: ignore[arg-type]
        eodhd_client=_DelistedEodhdClient(),  # type: ignore[arg-type]
    )

    assert result.gate_status == "rejected"
    assert isinstance(result, RejectedCandidateGate)
    assert result.is_actively_trading is False


@pytest.mark.anyio
async def test_validate_candidate_happy_path_us_ticker() -> None:
    candidate = _candidate(
        ticker="FLXS",
        company_name="Flexsteel Industries Inc",
        exchange=Exchange.NASDAQ,
    )
    fmp = _RecordingFmpClient(
        profile_rows=[
            {
                "symbol": "FLXS",
                "companyName": "Flexsteel Industries, Inc.",
                "exchange": "NASDAQ",
                "isActivelyTrading": True,
            }
        ],
    )
    settings = dashboard_settings_for_tests()

    result = await validate_candidate(
        candidate,
        settings=settings,
        fmp_client=fmp,  # type: ignore[arg-type]
    )

    assert result.gate_status == "passed"
    assert result.resolved_ticker == "FLXS"
    assert result.lane_context is not None
    assert result.lane_context.ticker == "FLXS"


def test_company_name_similarity_normalises_suffixes() -> None:
    assert (
        company_name_similarity("Ultimate Products plc", "Ultimate Products PLC") >= 0.9
    )


def test_candidate_to_lane_context_matches_gate_output_shape() -> None:
    candidate = _candidate(ticker="ULT.L", company_name="Ultimate Products plc")
    lane_context = candidate.to_lane_context(resolved_ticker="ULTP.L")
    assert lane_context.ticker == "ULTP.L"
