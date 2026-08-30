"""Allocation invariant checks that never clip, normalise, or repair weights."""

from collections import defaultdict
from collections.abc import Iterable, Sequence
from typing import Protocol

from discount_analyst.domain.allocations.constants import (
    COMPANY_WEIGHT_CAP_PCT,
    WEIGHT_SUM_TOLERANCE_PP,
)


class AllocationInvariantError(ValueError):
    """A proposal or persisted allocation violated a hard numeric invariant."""


class SharedRiskClusterShape(Protocol):
    label: str
    member_tickers: tuple[str, ...]


def require_unique_casefold(
    labels: Iterable[str],
    *,
    item_kind: str,
) -> dict[str, str]:
    seen: dict[str, str] = {}
    for label in labels:
        key = label.casefold()
        previous = seen.get(key)
        if previous is not None:
            msg = (
                f"{item_kind} must be unique case-insensitively; "
                f"{previous!r} and {label!r} collide."
            )
            raise ValueError(msg)
        seen[key] = label
    return seen


def validate_shared_risk_clusters(
    clusters: Sequence[SharedRiskClusterShape],
    *,
    known_ticker_keys: frozenset[str] | None = None,
) -> None:
    require_unique_casefold(
        (cluster.label for cluster in clusters),
        item_kind="Shared-risk cluster labels",
    )
    for cluster in clusters:
        if len(cluster.member_tickers) < 2:
            msg = (
                f"Shared-risk cluster {cluster.label!r} must name at least "
                "two member tickers."
            )
            raise ValueError(msg)
        require_unique_casefold(
            cluster.member_tickers,
            item_kind=f"Shared-risk cluster {cluster.label!r} tickers",
        )
        if known_ticker_keys is None:
            continue
        for ticker in cluster.member_tickers:
            if ticker.casefold() not in known_ticker_keys:
                msg = (
                    f"Shared-risk cluster {cluster.label!r} names unknown "
                    f"ticker {ticker!r}."
                )
                raise ValueError(msg)


def validate_ordered_weight_range(
    *,
    low_pct: float,
    target_pct: float,
    high_pct: float,
    label: str,
) -> None:
    if not 0 <= low_pct <= target_pct <= high_pct:
        msg = (
            f"{label} must satisfy 0 <= low <= target <= high; "
            f"got low={low_pct}, target={target_pct}, high={high_pct}."
        )
        raise AllocationInvariantError(msg)
    if high_pct > 100:
        msg = f"{label} range upper bound {high_pct} exceeds 100%."
        raise AllocationInvariantError(msg)


def validate_forced_zero_weights(
    *,
    low_pct: float,
    target_pct: float,
    high_pct: float,
    ticker: str,
) -> None:
    if (low_pct, target_pct, high_pct) != (0.0, 0.0, 0.0):
        msg = (
            f"Forced-zero position {ticker!r} must be exactly [0, 0, 0]; "
            f"got low={low_pct}, target={target_pct}, high={high_pct}."
        )
        raise AllocationInvariantError(msg)


def validate_retain_or_reduce_weights(
    *,
    target_pct: float,
    high_pct: float,
    current_weight_pct: float,
    ticker: str,
) -> None:
    if target_pct > current_weight_pct or high_pct > current_weight_pct:
        msg = (
            f"Retain-or-reduce position {ticker!r} cannot have target "
            f"{target_pct} or upper bound {high_pct} above current weight "
            f"{current_weight_pct}."
        )
        raise AllocationInvariantError(msg)


def validate_company_weight_caps(
    rows: Sequence[tuple[str, float, float]],
) -> None:
    """``rows`` are ``(company_name, target_pct, high_pct)``."""
    targets: dict[str, float] = defaultdict(float)
    highs: dict[str, float] = defaultdict(float)
    labels: dict[str, str] = {}
    for company_name, target_pct, high_pct in rows:
        key = company_name.casefold()
        labels.setdefault(key, company_name)
        targets[key] += target_pct
        highs[key] += high_pct
    for key, total_target in targets.items():
        company_name = labels[key]
        if total_target > COMPANY_WEIGHT_CAP_PCT:
            msg = (
                f"Company {company_name!r} target weights sum to "
                f"{total_target}, above the {COMPANY_WEIGHT_CAP_PCT}% cap. "
                "Differently spelt dual listings cannot be recognised until "
                "the domain gains a canonical issuer identifier."
            )
            raise AllocationInvariantError(msg)
        total_high = highs[key]
        if total_high > COMPANY_WEIGHT_CAP_PCT:
            msg = (
                f"Company {company_name!r} range upper bounds sum to "
                f"{total_high}, above the {COMPANY_WEIGHT_CAP_PCT}% cap."
            )
            raise AllocationInvariantError(msg)


def validate_portfolio_weight_totals(
    *,
    equity_target_pcts: Sequence[float],
    cash_target_pct: float,
    range_low_pcts: Sequence[float],
    range_high_pcts: Sequence[float],
) -> None:
    target_total = sum(equity_target_pcts) + cash_target_pct
    if abs(target_total - 100.0) > WEIGHT_SUM_TOLERANCE_PP:
        msg = (
            "Equity plus cash targets must total 100% "
            f"(within {WEIGHT_SUM_TOLERANCE_PP} percentage points); "
            f"got {target_total}."
        )
        raise AllocationInvariantError(msg)
    low_total = sum(range_low_pcts)
    if low_total > 100.0:
        msg = f"Range lower bounds sum to {low_total}, which exceeds 100%."
        raise AllocationInvariantError(msg)
    high_total = sum(range_high_pcts)
    if high_total < 100.0:
        msg = f"Range upper bounds sum to {high_total}, which is below 100%."
        raise AllocationInvariantError(msg)
