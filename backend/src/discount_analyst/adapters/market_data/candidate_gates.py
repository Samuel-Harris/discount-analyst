"""Deterministic pre-Researcher candidate gates: ticker resolution and listing status."""

from __future__ import annotations

import asyncio
import re
from collections.abc import Awaitable
from difflib import SequenceMatcher

from httpx import HTTPStatusError, TransportError
from pydantic import ValidationError

from discount_analyst.adapters.market_data.eodhd_client import EodhdClient
from discount_analyst.adapters.market_data.fmp_client import (
    FmpAccessDeniedError,
    FmpClient,
    FmpSearchResult,
)
from discount_analyst.agents.surveyor.schema import (
    Exchange,
    SurveyorCandidate,
)
from discount_analyst.application.candidates.gate_results import (
    CandidateGateResult,
    ListingDelisted,
    ListingProbe,
    PassedCandidateGate,
    RejectedCandidateGate,
    TickerResolution,
)

_PROFILE_MATCH_THRESHOLD = 0.55
_SEARCH_MATCH_THRESHOLD = 0.75

_EXCHANGE_FMP_ALIASES: dict[Exchange, frozenset[str]] = {
    Exchange.LSE: frozenset({"LSE", "LON", "LONDON STOCK EXCHANGE"}),
    Exchange.AIM: frozenset({"AIM", "LSE", "LON", "LONDON STOCK EXCHANGE"}),
    Exchange.NYSE: frozenset({"NYSE", "NEW YORK STOCK EXCHANGE"}),
    Exchange.NASDAQ: frozenset(
        {
            "NASDAQ",
            "NASDAQ GLOBAL SELECT",
            "NASDAQ GLOBAL MARKET",
            "NASDAQ CAPITAL MARKET",
        }
    ),
}


def company_name_similarity(left: str, right: str) -> float:
    """Ratio in [0, 1] after normalising legal suffixes and punctuation."""
    normalised_left = _normalise_company_name(left)
    normalised_right = _normalise_company_name(right)
    if not normalised_left or not normalised_right:
        return 0.0
    return SequenceMatcher(None, normalised_left, normalised_right).ratio()


def _normalise_company_name(name: str) -> str:
    lowered = name.casefold().strip()
    for suffix in (
        " public limited company",
        " plc",
        " limited",
        " ltd",
        " incorporated",
        " inc",
        " corporation",
        " corp",
        " group",
        " holdings",
        " co",
    ):
        if lowered.endswith(suffix):
            lowered = lowered[: -len(suffix)].strip()
    return re.sub(r"[^a-z0-9]", "", lowered)


def _exchange_matches(candidate_exchange: Exchange, fmp_exchange: str | None) -> bool:
    if fmp_exchange is None:
        return False
    normalised = fmp_exchange.strip().casefold()
    return normalised in {
        alias.casefold() for alias in _EXCHANGE_FMP_ALIASES[candidate_exchange]
    }


async def validate_candidate(
    candidate: SurveyorCandidate,
    *,
    fmp_api_key: str,
    eodhd_api_key: str,
    eodhd_disabled: bool = False,
    fmp_client: FmpClient | None = None,
    eodhd_client: EodhdClient | None = None,
) -> CandidateGateResult:
    """Resolve ticker and verify listing status before downstream agent lanes run."""
    source_ticker = candidate.ticker
    fmp = fmp_client or FmpClient(fmp_api_key)
    eodhd = eodhd_client
    if eodhd is None and not eodhd_disabled:
        eodhd = EodhdClient(eodhd_api_key)

    resolution = await _resolve_ticker(candidate, fmp=fmp)
    listing = await _check_listing_status(
        resolution.resolved_ticker,
        fmp=fmp,
        eodhd=eodhd,
        eodhd_disabled=eodhd_disabled,
    )
    notes = f"{resolution.resolution_notes} {listing.resolution_notes}"
    if isinstance(listing, ListingDelisted):
        return RejectedCandidateGate(
            source_ticker=source_ticker,
            resolved_ticker=resolution.resolved_ticker,
            resolution_notes=notes,
            gate_failure_reason=listing.gate_failure_reason,
            is_actively_trading=False,
            data_source=listing.data_source,
        )
    return PassedCandidateGate(
        source_ticker=source_ticker,
        resolved_ticker=resolution.resolved_ticker,
        resolution_notes=notes,
        is_actively_trading=True,
        data_source=listing.data_source,
        lane_context=candidate.to_lane_context(
            resolved_ticker=resolution.resolved_ticker,
        ),
    )


async def _resolve_ticker(
    candidate: SurveyorCandidate,
    *,
    fmp: FmpClient,
) -> TickerResolution:
    source_ticker = candidate.ticker
    notes: list[str] = []
    try:
        profiles = await fmp.profile(source_ticker)
    except FmpAccessDeniedError as exc:
        return await _resolve_via_search(candidate, fmp=fmp, notes=[str(exc)])

    if profiles:
        profile = profiles[0]
        similarity = company_name_similarity(
            candidate.company_name, profile.company_name
        )
        notes.append(
            f"FMP profile for {source_ticker!r} returned {profile.company_name!r} "
            f"(similarity {similarity:.2f})."
        )
        if similarity >= _PROFILE_MATCH_THRESHOLD:
            resolved = profile.symbol or source_ticker
            if resolved != source_ticker:
                notes.append(f"Auto-corrected ticker {source_ticker!r} → {resolved!r}.")
            return _resolution(candidate, notes, resolved)

    return await _resolve_via_search(
        candidate,
        fmp=fmp,
        notes=notes or [f"FMP profile empty or name mismatch for {source_ticker!r}."],
    )


def _fmp_search_queries(source_ticker: str, company_name: str) -> list[str]:
    queries = [source_ticker]
    if source_ticker.casefold().endswith(".l"):
        stem = source_ticker[:-2]
        if stem and all(stem.casefold() != query.casefold() for query in queries):
            queries.append(stem)
    if company_name.strip() and all(
        company_name.casefold() != query.casefold() for query in queries
    ):
        queries.append(company_name)
    return queries


async def _search_symbol_rows(
    fmp: FmpClient,
    queries: list[str],
    notes: list[str],
) -> list[FmpSearchResult]:
    seen_symbols: set[str] = set()
    rows: list[FmpSearchResult] = []
    for query in queries:
        try:
            found = await fmp.search_symbol(query)
        except FmpAccessDeniedError as exc:
            notes.append(
                f"FMP symbol search denied for {query!r} (HTTP {exc.status_code})."
            )
            continue
        for row in found:
            symbol_key = row.symbol.casefold()
            if symbol_key in seen_symbols:
                continue
            seen_symbols.add(symbol_key)
            rows.append(row)
    return rows


async def _resolve_via_search(
    candidate: SurveyorCandidate,
    *,
    fmp: FmpClient,
    notes: list[str],
) -> TickerResolution:
    source_ticker = candidate.ticker
    queries = _fmp_search_queries(source_ticker, candidate.company_name)
    results = await _search_symbol_rows(fmp, queries, notes)
    if not results and any("symbol search denied" in note for note in notes):
        notes.append(
            f"FMP symbol search denied for {queries!r}; keeping source ticker."
        )
        return _resolution(candidate, notes, source_ticker)

    exact_matches = [
        row
        for row in results
        if row.symbol.casefold() == source_ticker.casefold()
        and _exchange_matches(candidate.exchange, row.exchange)
    ]
    exchange_matches = [
        row for row in results if _exchange_matches(candidate.exchange, row.exchange)
    ]
    strong_matches = [
        row
        for row in exchange_matches
        if company_name_similarity(candidate.company_name, row.name)
        >= _SEARCH_MATCH_THRESHOLD
    ]
    notes.append(
        f"FMP search queries {queries} returned {len(results)} unique row(s); "
        f"{len(exchange_matches)} on {candidate.exchange.value}; "
        f"{len(strong_matches)} strong name match(es)."
    )

    resolved = (
        exact_matches[0].symbol
        if exact_matches
        else (strong_matches[0].symbol if len(strong_matches) == 1 else None)
    )
    if resolved is not None:
        if resolved != source_ticker:
            notes.append(f"Search resolved {source_ticker!r} → {resolved!r}.")
        return _resolution(candidate, notes, resolved)

    if len(strong_matches) > 1:
        symbols = ", ".join(sorted({row.symbol for row in strong_matches}))
        notes.append(
            f"Ambiguous FMP search matches for {candidate.company_name!r}: {symbols}; "
            "keeping source ticker."
        )
    else:
        notes.append(
            f"No confident FMP symbol match for {candidate.company_name!r} "
            f"on {candidate.exchange.value} (source ticker {source_ticker!r}); "
            "keeping source ticker."
        )
    return _resolution(candidate, notes, source_ticker)


def _resolution(
    candidate: SurveyorCandidate,
    notes: list[str],
    resolved_ticker: str,
) -> TickerResolution:
    return TickerResolution(
        source_ticker=candidate.ticker,
        resolved_ticker=resolved_ticker,
        resolution_notes=" ".join(notes),
        data_source="fmp",
    )


async def _check_listing_status(
    resolved_ticker: str,
    *,
    fmp: FmpClient,
    eodhd: EodhdClient | None,
    eodhd_disabled: bool,
) -> ListingProbe | ListingDelisted:
    denied: FmpAccessDeniedError | None = None
    try:
        profiles = await fmp.profile(resolved_ticker)
    except FmpAccessDeniedError as exc:
        denied = exc
        profiles = []

    profile = profiles[0] if profiles else None
    actively_trading = profile.is_actively_trading if profile else None

    if actively_trading is True:
        return ListingProbe(
            resolution_notes="FMP profile indicates active listing.",
            data_source="fmp",
        )

    if (
        eodhd is not None
        and not eodhd_disabled
        and resolved_ticker.casefold().endswith(".l")
    ):
        eodhd_notes = (
            str(denied)
            if denied is not None
            else (
                "FMP listing probe inconclusive "
                f"(profile present={profile is not None}, "
                f"isActivelyTrading={actively_trading})."
            )
        )
        return await _check_listing_via_eodhd(
            resolved_ticker,
            eodhd=eodhd,
            resolution_notes=eodhd_notes,
        )

    if actively_trading is False:
        return ListingDelisted(
            resolution_notes="FMP listing probe failed.",
            gate_failure_reason=(
                f"{resolved_ticker!r} is not actively trading: "
                "isActivelyTrading is false."
            ),
            data_source="fmp",
        )

    if denied is not None:
        return ListingProbe(
            resolution_notes=(
                f"{denied} Listing unconfirmed: FMP listing probe denied for "
                f"{resolved_ticker!r} (HTTP {denied.status_code})."
            ),
            data_source="fmp",
        )
    return ListingProbe(
        resolution_notes=(
            "FMP listing unconfirmed "
            f"(profile present={profile is not None}, "
            f"isActivelyTrading={actively_trading})."
        ),
        data_source="fmp",
    )


async def _check_listing_via_eodhd(
    resolved_ticker: str,
    *,
    eodhd: EodhdClient,
    resolution_notes: str,
) -> ListingProbe | ListingDelisted:
    (quote, quote_error), (general, general_error) = await asyncio.gather(
        _eodhd_listing_call(eodhd.real_time(resolved_ticker)),
        _eodhd_listing_call(eodhd.fundamentals_general(resolved_ticker)),
    )

    if general is not None and general.is_delisted is True:
        return ListingDelisted(
            resolution_notes=resolution_notes,
            gate_failure_reason=(
                f"{resolved_ticker!r} is not actively trading: "
                "EODHD marks symbol as delisted."
            ),
            data_source="eodhd",
        )

    error_bits = [bit for bit in (quote_error, general_error) if bit is not None]
    has_positive_close = (
        quote is not None and quote.close is not None and quote.close > 0
    )
    if error_bits:
        note = f"EODHD listing unconfirmed ({'; '.join(error_bits)})."
    elif quote is None and general is None:
        note = "EODHD listing unconfirmed (no real-time quote and no fundamentals)."
    elif has_positive_close:
        note = "EODHD real-time quote present."
    else:
        note = "EODHD real-time close unavailable; symbol not marked delisted."
    return ListingProbe(
        resolution_notes=f"{resolution_notes} {note}",
        data_source="eodhd",
    )


async def _eodhd_listing_call[T](
    awaitable: Awaitable[T],
) -> tuple[T | None, str | None]:
    try:
        return await awaitable, None
    except HTTPStatusError as exc:
        return None, f"httpx.HTTPStatusError HTTP {exc.response.status_code}"
    except TransportError as exc:
        return None, f"httpx.{type(exc).__name__}"
    except ValidationError:
        return None, "pydantic.ValidationError"
    except ValueError as exc:
        return None, type(exc).__name__
