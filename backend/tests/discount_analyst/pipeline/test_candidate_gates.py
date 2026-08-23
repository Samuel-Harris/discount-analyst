"""Tests for pre-Researcher candidate gates."""

from __future__ import annotations

from dataclasses import dataclass

import httpx
import pytest

from pydantic import ValidationError

from discount_analyst.adapters.simulation.mock_outputs import (
    mock_key_metrics,
    mock_surveyor_candidate,
)
from discount_analyst.config.testing_settings import dashboard_settings_for_tests
from discount_analyst.agents.surveyor.schema import (
    Exchange,
    SurveyorCandidate,
)
from discount_analyst.adapters.market_data.eodhd_client import (
    EodhdGeneralInfo,
    EodhdRealTimeQuote,
)
from discount_analyst.adapters.market_data.fmp_client import (
    FmpAccessDeniedError,
    FmpProfile,
    FmpSearchResult,
)
from discount_analyst.application.candidates.gate_results import CandidateGateResult
from discount_analyst.adapters.market_data.candidate_gates import (
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
        profile_rows: list[dict[str, object]] | None = None,
        search_by_query: dict[str, list[dict[str, object]]] | None = None,
        denied_profile_symbols: frozenset[str] = frozenset(),
        denied_profile_status: int = 402,
        denied_search_queries: frozenset[str] = frozenset(),
    ) -> None:
        self._profile_rows = profile_rows or []
        self._search_by_query = {
            query.casefold(): rows for query, rows in (search_by_query or {}).items()
        }
        self._denied_profile_symbols = {
            symbol.casefold() for symbol in denied_profile_symbols
        }
        self._denied_profile_status = denied_profile_status
        self._denied_search_queries = {
            query.casefold() for query in denied_search_queries
        }
        self.search_queries: list[str] = []

    async def profile(self, symbol: str) -> list[FmpProfile]:
        if symbol.casefold() in self._denied_profile_symbols:
            raise FmpAccessDeniedError(
                status_code=self._denied_profile_status, symbol_or_query=symbol
            )
        return [FmpProfile.model_validate(row) for row in self._profile_rows]

    async def search_symbol(self, query: str) -> list[FmpSearchResult]:
        self.search_queries.append(query)
        if query.casefold() in self._denied_search_queries:
            raise FmpAccessDeniedError(
                status_code=self._denied_profile_status, symbol_or_query=query
            )
        rows = self._search_by_query.get(query.casefold(), [])
        return [FmpSearchResult.model_validate(row) for row in rows]


@dataclass(frozen=True, slots=True)
class _StubEodhdClient:
    close: float | None = 278.5
    is_delisted: bool | None = False
    quote_missing: bool = False
    general_missing: bool = False
    fundamentals_http_status: int | None = None
    quote_exception: Exception | None = None

    async def real_time(self, symbol: str) -> EodhdRealTimeQuote | None:
        if self.quote_exception is not None:
            raise self.quote_exception
        if self.quote_missing:
            return None
        return EodhdRealTimeQuote(code=symbol, close=self.close)

    async def fundamentals_general(self, symbol: str) -> EodhdGeneralInfo | None:
        if self.fundamentals_http_status is not None:
            request = httpx.Request(
                "GET", f"https://eodhd.com/api/fundamentals/{symbol}"
            )
            response = httpx.Response(self.fundamentals_http_status, request=request)
            raise httpx.HTTPStatusError(
                str(self.fundamentals_http_status),
                request=request,
                response=response,
            )
        if self.general_missing:
            return None
        return EodhdGeneralInfo(code=symbol, IsDelisted=self.is_delisted)


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
        search_by_query={
            "Ultimate Products plc": [
                {
                    "symbol": "ULTP.L",
                    "name": "Ultimate Products plc",
                    "exchange": "LSE",
                }
            ]
        },
    )
    settings = dashboard_settings_for_tests()

    result = await validate_candidate(
        candidate,
        fmp_api_key=settings.fmp.api_key,
        eodhd_api_key=settings.eodhd.api_key,
        eodhd_disabled=settings.eodhd.disabled,
        fmp_client=fmp,  # type: ignore[arg-type]
    )

    assert result.gate_status == "passed"
    assert result.resolved_ticker == "ULTP.L"
    assert result.lane_context is not None
    assert result.lane_context.ticker == "ULTP.L"
    assert "market_cap_local" not in result.lane_context.model_dump()
    assert fmp.search_queries == ["ULT.L", "ULT", "Ultimate Products plc"]


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
        fmp_api_key=settings.fmp.api_key,
        eodhd_api_key=settings.eodhd.api_key,
        eodhd_disabled=settings.eodhd.disabled,
        fmp_client=fmp,  # type: ignore[arg-type]
        eodhd_client=_StubEodhdClient(quote_missing=True, is_delisted=True),  # type: ignore[arg-type]
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
        fmp_api_key=settings.fmp.api_key,
        eodhd_api_key=settings.eodhd.api_key,
        eodhd_disabled=settings.eodhd.disabled,
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


@pytest.mark.anyio
async def test_validate_candidate_passes_us_ticker_when_fmp_profile_denied() -> None:
    candidate = _candidate(
        ticker="AOUT",
        company_name="American Outdoor Brands Inc",
        exchange=Exchange.NASDAQ,
    )
    settings = dashboard_settings_for_tests()

    result = await validate_candidate(
        candidate,
        fmp_api_key=settings.fmp.api_key,
        eodhd_api_key=settings.eodhd.api_key,
        eodhd_disabled=settings.eodhd.disabled,
        fmp_client=_RecordingFmpClient(
            profile_rows=[],
            denied_profile_symbols=frozenset({"AOUT"}),
        ),  # type: ignore[arg-type]
    )

    assert result.gate_status == "passed"
    assert result.resolved_ticker == "AOUT"
    assert result.source_ticker == "AOUT"
    assert "unconfirmed" in result.resolution_notes.casefold()


_BOWL_LSE = {
    "symbol": "BOWL.L",
    "name": "Hollywood Bowl Group plc",
    "exchange": "LSE",
}
_BOWL_NYSE = {
    "symbol": "BOWL",
    "name": "Bowlero Corp",
    "exchange": "NYSE",
}


async def _validate_uk_denied_profile(
    *,
    ticker: str,
    company_name: str,
    search_by_query: dict[str, list[dict[str, object]]],
    eodhd_client: object | None = None,
    denied_search_queries: frozenset[str] = frozenset(),
) -> tuple[CandidateGateResult, _RecordingFmpClient]:
    candidate = _candidate(ticker=ticker, company_name=company_name)
    fmp = _RecordingFmpClient(
        profile_rows=[],
        denied_profile_symbols=frozenset({ticker}),
        search_by_query=search_by_query,
        denied_search_queries=denied_search_queries,
    )
    settings = dashboard_settings_for_tests()
    result = await validate_candidate(
        candidate,
        fmp_api_key=settings.fmp.api_key,
        eodhd_api_key=settings.eodhd.api_key,
        eodhd_disabled=settings.eodhd.disabled,
        fmp_client=fmp,  # type: ignore[arg-type]
        eodhd_client=(eodhd_client if eodhd_client is not None else _StubEodhdClient()),  # type: ignore[arg-type]
    )
    return result, fmp


@pytest.mark.anyio
async def test_validate_candidate_passes_bowl_l_when_profile_denied_and_search_hits_ticker() -> (
    None
):
    result, fmp = await _validate_uk_denied_profile(
        ticker="BOWL.L",
        company_name="Hollywood Bowl Group plc",
        search_by_query={"BOWL.L": [_BOWL_LSE]},
    )

    assert result.gate_status == "passed"
    assert result.resolved_ticker == "BOWL.L"
    assert result.data_source == "eodhd"
    assert fmp.search_queries[0] == "BOWL.L"


@pytest.mark.anyio
async def test_validate_candidate_keeps_bowl_l_when_stem_search_returns_nyse_and_lse() -> (
    None
):
    result, fmp = await _validate_uk_denied_profile(
        ticker="BOWL.L",
        company_name="Hollywood Bowl Group plc",
        search_by_query={"BOWL": [_BOWL_NYSE, _BOWL_LSE]},
    )

    assert result.gate_status == "passed"
    assert result.resolved_ticker == "BOWL.L"
    assert fmp.search_queries[:2] == ["BOWL.L", "BOWL"]


@pytest.mark.anyio
async def test_validate_candidate_passes_yu_l_exact_ticker_below_name_threshold() -> (
    None
):
    result, _fmp = await _validate_uk_denied_profile(
        ticker="YU.L",
        company_name="Yu Group",
        search_by_query={
            "YU.L": [
                {
                    "symbol": "YU.L",
                    "name": "Yü Group PLC",
                    "exchange": "LSE",
                }
            ]
        },
    )

    assert company_name_similarity("Yu Group", "Yü Group PLC") < 0.75
    assert result.gate_status == "passed"
    assert result.resolved_ticker == "YU.L"


_BOWL_DENIED_SEARCH = {"BOWL.L": [_BOWL_LSE]}


@pytest.mark.anyio
async def test_validate_candidate_passes_when_eodhd_close_is_na_and_not_delisted() -> (
    None
):
    result, _fmp = await _validate_uk_denied_profile(
        ticker="BOWL.L",
        company_name="Hollywood Bowl Group plc",
        search_by_query=_BOWL_DENIED_SEARCH,
        eodhd_client=_StubEodhdClient(close=None, is_delisted=False),
    )

    assert result.gate_status == "passed"
    assert result.is_actively_trading is True
    assert result.data_source == "eodhd"
    assert "close unavailable" in result.resolution_notes


@pytest.mark.anyio
async def test_validate_candidate_rejects_when_eodhd_close_is_na_and_delisted() -> None:
    result, _fmp = await _validate_uk_denied_profile(
        ticker="BOWL.L",
        company_name="Hollywood Bowl Group plc",
        search_by_query=_BOWL_DENIED_SEARCH,
        eodhd_client=_StubEodhdClient(close=None, is_delisted=True),
    )

    assert result.gate_status == "rejected"
    assert isinstance(result, RejectedCandidateGate)
    assert result.is_actively_trading is False
    assert result.data_source == "eodhd"
    assert "EODHD marks symbol as delisted" in result.gate_failure_reason


@pytest.mark.anyio
async def test_validate_candidate_passes_when_eodhd_quote_and_fundamentals_missing() -> (
    None
):
    result, _fmp = await _validate_uk_denied_profile(
        ticker="BOWL.L",
        company_name="Hollywood Bowl Group plc",
        search_by_query=_BOWL_DENIED_SEARCH,
        eodhd_client=_StubEodhdClient(quote_missing=True, general_missing=True),
    )

    assert result.gate_status == "passed"
    assert result.is_actively_trading is True
    assert "unconfirmed" in result.resolution_notes.casefold()


@pytest.mark.anyio
async def test_validate_candidate_admits_source_ticker_when_fmp_search_empty() -> None:
    candidate = _candidate(ticker="ZZZ.L", company_name="Unknown Widgets plc")
    fmp = _RecordingFmpClient(profile_rows=[], search_by_query={})
    settings = dashboard_settings_for_tests()

    result = await validate_candidate(
        candidate,
        fmp_api_key=settings.fmp.api_key,
        eodhd_api_key=settings.eodhd.api_key,
        eodhd_disabled=settings.eodhd.disabled,
        fmp_client=fmp,  # type: ignore[arg-type]
        eodhd_client=_StubEodhdClient(is_delisted=False),  # type: ignore[arg-type]
    )

    assert result.gate_status == "passed"
    assert result.resolved_ticker == "ZZZ.L"
    assert result.source_ticker == "ZZZ.L"
    assert "keeping source ticker" in result.resolution_notes


@pytest.mark.anyio
async def test_validate_candidate_keeps_source_ticker_when_two_strong_lse_matches() -> (
    None
):
    candidate = _candidate(ticker="FOO.L", company_name="Acme Industries")
    fmp = _RecordingFmpClient(
        profile_rows=[],
        search_by_query={
            "Acme Industries": [
                {
                    "symbol": "ACME.L",
                    "name": "Acme Industries plc",
                    "exchange": "LSE",
                },
                {
                    "symbol": "ACMI.L",
                    "name": "Acme Industries Group plc",
                    "exchange": "LSE",
                },
            ]
        },
    )
    settings = dashboard_settings_for_tests()

    result = await validate_candidate(
        candidate,
        fmp_api_key=settings.fmp.api_key,
        eodhd_api_key=settings.eodhd.api_key,
        eodhd_disabled=settings.eodhd.disabled,
        fmp_client=fmp,  # type: ignore[arg-type]
        eodhd_client=_StubEodhdClient(is_delisted=False),  # type: ignore[arg-type]
    )

    assert company_name_similarity("Acme Industries", "Acme Industries plc") >= 0.75
    assert (
        company_name_similarity("Acme Industries", "Acme Industries Group plc") >= 0.75
    )
    assert result.gate_status == "passed"
    assert result.resolved_ticker == "FOO.L"
    assert result.resolved_ticker not in {"ACME.L", "ACMI.L"}
    assert "Ambiguous FMP search matches" in result.resolution_notes


@pytest.mark.anyio
async def test_validate_candidate_rejects_nasdaq_when_not_actively_trading() -> None:
    candidate = _candidate(
        ticker="DEAD",
        company_name="Dead Co Inc",
        exchange=Exchange.NASDAQ,
    )
    fmp = _RecordingFmpClient(
        profile_rows=[
            {
                "symbol": "DEAD",
                "companyName": "Dead Co Inc",
                "exchange": "NASDAQ",
                "isActivelyTrading": False,
            }
        ],
    )
    settings = dashboard_settings_for_tests()

    result = await validate_candidate(
        candidate,
        fmp_api_key=settings.fmp.api_key,
        eodhd_api_key=settings.eodhd.api_key,
        eodhd_disabled=settings.eodhd.disabled,
        fmp_client=fmp,  # type: ignore[arg-type]
    )

    assert result.gate_status == "rejected"
    assert isinstance(result, RejectedCandidateGate)
    assert result.is_actively_trading is False
    assert result.data_source == "fmp"
    assert "isActivelyTrading is false" in result.gate_failure_reason


@pytest.mark.anyio
async def test_validate_candidate_passes_when_eodhd_fundamentals_http_403() -> None:
    result, _fmp = await _validate_uk_denied_profile(
        ticker="BOWL.L",
        company_name="Hollywood Bowl Group plc",
        search_by_query=_BOWL_DENIED_SEARCH,
        eodhd_client=_StubEodhdClient(fundamentals_http_status=403),
    )

    assert result.gate_status == "passed"
    assert result.is_actively_trading is True
    assert "unconfirmed" in result.resolution_notes.casefold()
    assert "httpx.HTTPStatusError HTTP 403" in result.resolution_notes


@pytest.mark.anyio
async def test_validate_candidate_continues_search_when_ticker_query_denied() -> None:
    result, fmp = await _validate_uk_denied_profile(
        ticker="BOWL.L",
        company_name="Hollywood Bowl Group plc",
        search_by_query={"BOWL": [_BOWL_LSE]},
        denied_search_queries=frozenset({"BOWL.L"}),
    )

    assert result.gate_status == "passed"
    assert result.resolved_ticker == "BOWL.L"
    assert fmp.search_queries[:2] == ["BOWL.L", "BOWL"]
    assert any(
        "BOWL.L" in note and "denied" in note.casefold()
        for note in [result.resolution_notes]
    )


@pytest.mark.anyio
async def test_validate_candidate_passes_when_eodhd_quote_validation_fails() -> None:
    result, _fmp = await _validate_uk_denied_profile(
        ticker="BOWL.L",
        company_name="Hollywood Bowl Group plc",
        search_by_query=_BOWL_DENIED_SEARCH,
        eodhd_client=_StubEodhdClient(
            quote_exception=ValidationError.from_exception_data(
                "EodhdRealTimeQuote",
                [],
            ),
        ),
    )

    assert result.gate_status == "passed"
    assert "pydantic.ValidationError" in result.resolution_notes
