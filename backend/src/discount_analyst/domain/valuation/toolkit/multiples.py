"""Comparable-multiple valuation helpers."""

from __future__ import annotations

from statistics import median


def peer_multiple_summary(peer_multiples: list[float]) -> dict[str, float]:
    if not peer_multiples:
        raise ValueError("peer_multiples must not be empty.")
    values = sorted(peer_multiples)
    return {
        "min": values[0],
        "median": median(values),
        "max": values[-1],
        "count": float(len(values)),
    }


def equity_value_from_enterprise_multiple(
    *,
    financial_metric: float,
    enterprise_value_multiple: float,
    net_debt: float,
) -> float:
    enterprise_value = financial_metric * enterprise_value_multiple
    return enterprise_value - net_debt


def per_share_value(
    *,
    equity_value: float,
    shares_outstanding: float,
) -> float:
    if shares_outstanding <= 0:
        msg = f"shares_outstanding must be positive, got {shares_outstanding}."
        raise ValueError(msg)
    return equity_value / shares_outstanding


def peer_multiple_valuation(
    *,
    peer_multiples: list[float],
    target_financial_metric: float,
    net_debt: float,
    shares_outstanding: float,
    selected_multiple: float | None = None,
) -> dict[str, float]:
    """Value equity from a peer EV multiple and target company metric."""
    summary = peer_multiple_summary(peer_multiples)
    multiple = selected_multiple if selected_multiple is not None else summary["median"]
    equity_value = equity_value_from_enterprise_multiple(
        financial_metric=target_financial_metric,
        enterprise_value_multiple=multiple,
        net_debt=net_debt,
    )
    return {
        "selected_multiple": multiple,
        "peer_min_multiple": summary["min"],
        "peer_median_multiple": summary["median"],
        "peer_max_multiple": summary["max"],
        "equity_value": equity_value,
        "value_per_share": per_share_value(
            equity_value=equity_value,
            shares_outstanding=shares_outstanding,
        ),
    }
