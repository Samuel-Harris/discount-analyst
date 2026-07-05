"""Deterministic pre-Researcher candidate gates: ticker resolution and listing status."""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Literal

from pydantic import BaseModel

from common.config import Settings
from discount_analyst.agents.surveyor.schema import (
    Exchange,
    SurveyorCandidate,
    SurveyorLaneContext,
)
from discount_analyst.integrations.eodhd_client import EodhdClient
from discount_analyst.integrations.fmp_client import (
    FmpAccessDeniedError,
    FmpClient,
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


type GateDataSource = Literal["fmp", "eodhd", "mock"]


class TickerResolution(BaseModel):
    source_ticker: str
    resolved_ticker: str
    resolution_notes: str
    data_source: GateDataSource


class ListingProbe(BaseModel):
    resolution_notes: str
    is_actively_trading: bool
    data_source: GateDataSource


class PassedCandidateGate(BaseModel):
    gate_status: Literal["passed"] = "passed"
    source_ticker: str
    resolved_ticker: str
    resolution_notes: str
    is_actively_trading: bool
    data_source: GateDataSource
    lane_context: SurveyorLaneContext


class RejectedCandidateGate(BaseModel):
    gate_status: Literal["rejected"] = "rejected"
    source_ticker: str
    resolved_ticker: str | None
    resolution_notes: str
    gate_failure_reason: str
    is_actively_trading: bool | None
    data_source: GateDataSource


type CandidateGateResult = PassedCandidateGate | RejectedCandidateGate


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
    settings: Settings,
    fmp_client: FmpClient | None = None,
    eodhd_client: EodhdClient | None = None,
) -> CandidateGateResult:
    """Resolve ticker and verify listing status before downstream agent lanes run."""
    source_ticker = candidate.ticker
    fmp = fmp_client or FmpClient(settings.fmp.api_key)
    eodhd = eodhd_client
    if eodhd is None and not settings.eodhd.disabled:
        eodhd = EodhdClient(settings.eodhd.api_key)

    resolution = await _resolve_ticker(candidate, fmp=fmp)
    if isinstance(resolution, RejectedCandidateGate):
        return resolution

    listing = await _check_listing_status(
        resolution.resolved_ticker,
        fmp=fmp,
        eodhd=eodhd,
        eodhd_disabled=settings.eodhd.disabled,
    )
    if isinstance(listing, RejectedCandidateGate):
        return RejectedCandidateGate(
            source_ticker=source_ticker,
            resolved_ticker=resolution.resolved_ticker,
            resolution_notes=(
                f"{resolution.resolution_notes} {listing.resolution_notes}"
            ),
            gate_failure_reason=listing.gate_failure_reason,
            is_actively_trading=listing.is_actively_trading,
            data_source=listing.data_source,
        )

    lane_context = candidate.to_lane_context(
        resolved_ticker=resolution.resolved_ticker,
    )
    return PassedCandidateGate(
        source_ticker=source_ticker,
        resolved_ticker=resolution.resolved_ticker,
        resolution_notes=f"{resolution.resolution_notes} {listing.resolution_notes}",
        is_actively_trading=listing.is_actively_trading,
        data_source=listing.data_source,
        lane_context=lane_context,
    )


async def _resolve_ticker(
    candidate: SurveyorCandidate,
    *,
    fmp: FmpClient,
) -> TickerResolution | RejectedCandidateGate:
    source_ticker = candidate.ticker
    notes: list[str] = []
    try:
        profiles = await fmp.profile(source_ticker)
    except FmpAccessDeniedError as exc:
        if source_ticker.casefold().endswith(".l"):
            return await _resolve_via_search(candidate, fmp=fmp, notes=[str(exc)])
        return _rejection(
            source_ticker=source_ticker,
            resolved_ticker=None,
            resolution_notes=str(exc),
            gate_failure_reason=(
                f"FMP profile lookup denied for {source_ticker!r} (HTTP {exc.status_code})."
            ),
            data_source="fmp",
        )

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
            return TickerResolution(
                source_ticker=source_ticker,
                resolved_ticker=resolved,
                resolution_notes=" ".join(notes),
                data_source="fmp",
            )

    return await _resolve_via_search(
        candidate,
        fmp=fmp,
        notes=notes or [f"FMP profile empty or name mismatch for {source_ticker!r}."],
    )


async def _resolve_via_search(
    candidate: SurveyorCandidate,
    *,
    fmp: FmpClient,
    notes: list[str],
) -> TickerResolution | RejectedCandidateGate:
    source_ticker = candidate.ticker
    try:
        results = await fmp.search_symbol(candidate.company_name)
    except FmpAccessDeniedError as exc:
        return _rejection(
            source_ticker=source_ticker,
            resolved_ticker=None,
            resolution_notes=" ".join(notes + [str(exc)]),
            gate_failure_reason=(
                f"FMP symbol search denied for {candidate.company_name!r} "
                f"(HTTP {exc.status_code})."
            ),
            data_source="fmp",
        )

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
        f"FMP search returned {len(results)} row(s); "
        f"{len(exchange_matches)} on {candidate.exchange.value}; "
        f"{len(strong_matches)} strong name match(es)."
    )
    if len(strong_matches) == 1:
        resolved = strong_matches[0].symbol
        if resolved != source_ticker:
            notes.append(f"Search resolved {source_ticker!r} → {resolved!r}.")
        return TickerResolution(
            source_ticker=source_ticker,
            resolved_ticker=resolved,
            resolution_notes=" ".join(notes),
            data_source="fmp",
        )

    if len(strong_matches) > 1:
        symbols = ", ".join(sorted({row.symbol for row in strong_matches}))
        return _rejection(
            source_ticker=source_ticker,
            resolved_ticker=None,
            resolution_notes=" ".join(notes),
            gate_failure_reason=(
                f"Ambiguous FMP search matches for {candidate.company_name!r}: {symbols}."
            ),
            data_source="fmp",
        )

    return _rejection(
        source_ticker=source_ticker,
        resolved_ticker=None,
        resolution_notes=" ".join(notes),
        gate_failure_reason=(
            f"No confident FMP symbol match for {candidate.company_name!r} "
            f"on {candidate.exchange.value} (source ticker {source_ticker!r})."
        ),
        data_source="fmp",
    )


async def _check_listing_status(
    resolved_ticker: str,
    *,
    fmp: FmpClient,
    eodhd: EodhdClient | None,
    eodhd_disabled: bool,
) -> ListingProbe | RejectedCandidateGate:
    try:
        quotes = await fmp.quote_short(resolved_ticker)
        profiles = await fmp.profile(resolved_ticker)
    except FmpAccessDeniedError as exc:
        if (
            resolved_ticker.casefold().endswith(".l")
            and not eodhd_disabled
            and eodhd is not None
        ):
            return await _check_listing_via_eodhd(
                resolved_ticker,
                eodhd=eodhd,
                resolution_notes=str(exc),
            )
        return _rejection(
            source_ticker=resolved_ticker,
            resolved_ticker=resolved_ticker,
            resolution_notes=str(exc),
            gate_failure_reason=(
                f"FMP listing probe denied for {resolved_ticker!r} "
                f"(HTTP {exc.status_code})."
            ),
            data_source="fmp",
        )

    has_quote = bool(quotes) and quotes[0].price is not None and quotes[0].price > 0
    profile = profiles[0] if profiles else None
    actively_trading = profile.is_actively_trading if profile else None

    if has_quote and actively_trading is not False:
        return ListingProbe(
            resolution_notes="FMP quote-short and profile indicate active listing.",
            is_actively_trading=True,
            data_source="fmp",
        )

    if (
        resolved_ticker.casefold().endswith(".l")
        and not eodhd_disabled
        and eodhd is not None
    ):
        return await _check_listing_via_eodhd(
            resolved_ticker,
            eodhd=eodhd,
            resolution_notes=(
                "FMP listing probe inconclusive "
                f"(quote={has_quote}, isActivelyTrading={actively_trading})."
            ),
        )

    reason_parts: list[str] = []
    if not has_quote:
        reason_parts.append("no valid FMP quote-short")
    if actively_trading is False:
        reason_parts.append("isActivelyTrading is false")
    return _rejection(
        source_ticker=resolved_ticker,
        resolved_ticker=resolved_ticker,
        resolution_notes="FMP listing probe failed.",
        gate_failure_reason=(
            f"{resolved_ticker!r} is not actively trading: {', '.join(reason_parts)}."
        ),
        data_source="fmp",
        is_actively_trading=False,
    )


async def _check_listing_via_eodhd(
    resolved_ticker: str,
    *,
    eodhd: EodhdClient,
    resolution_notes: str,
) -> ListingProbe | RejectedCandidateGate:
    quote = await eodhd.real_time(resolved_ticker)
    general = await eodhd.fundamentals_general(resolved_ticker)
    has_price = quote is not None and quote.close is not None and quote.close > 0
    is_delisted = general is not None and general.is_delisted is True

    if has_price and not is_delisted:
        return ListingProbe(
            resolution_notes=f"{resolution_notes} EODHD real-time quote present.",
            is_actively_trading=True,
            data_source="eodhd",
        )

    reason_parts: list[str] = []
    if is_delisted:
        reason_parts.append("EODHD marks symbol as delisted")
    if not has_price:
        reason_parts.append("no valid EODHD real-time quote")
    return _rejection(
        source_ticker=resolved_ticker,
        resolved_ticker=resolved_ticker,
        resolution_notes=resolution_notes,
        gate_failure_reason=(
            f"{resolved_ticker!r} is not actively trading: {', '.join(reason_parts)}."
        ),
        data_source="eodhd",
        is_actively_trading=False,
    )


def _rejection(
    *,
    source_ticker: str,
    resolved_ticker: str | None,
    resolution_notes: str,
    gate_failure_reason: str,
    data_source: GateDataSource,
    is_actively_trading: bool | None = None,
) -> RejectedCandidateGate:
    return RejectedCandidateGate(
        source_ticker=source_ticker,
        resolved_ticker=resolved_ticker,
        resolution_notes=resolution_notes,
        gate_failure_reason=gate_failure_reason,
        is_actively_trading=is_actively_trading,
        data_source=data_source,
    )
