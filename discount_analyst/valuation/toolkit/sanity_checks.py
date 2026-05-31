"""Policy-free sanity checks for valuation outputs."""

from __future__ import annotations


def monotonic_percentile_check(
    *,
    p10: float,
    p25: float,
    p50: float,
    p75: float,
    p90: float,
) -> dict[str, str | bool]:
    ok = [p10, p25, p50, p75, p90] == sorted([p10, p25, p50, p75, p90])
    return {
        "check": "monotonic_percentiles",
        "ok": ok,
        "message": "Percentiles are monotonic."
        if ok
        else "Expected p10 <= p25 <= p50 <= p75 <= p90.",
    }


def expected_value_range_check(
    *,
    expected_value: float,
    p10: float,
    p90: float,
) -> dict[str, str | bool]:
    ok = p10 <= expected_value <= p90
    return {
        "check": "expected_value_range",
        "ok": ok,
        "message": "Expected value sits within p10-p90."
        if ok
        else "Expected value is outside p10-p90.",
    }


def terminal_value_share_check(
    *,
    terminal_value_present_value: float,
    enterprise_value: float,
    warning_threshold_pct: float = 75.0,
) -> dict[str, str | bool | float]:
    if enterprise_value == 0:
        raise ValueError("enterprise_value must not be zero.")
    share_pct = terminal_value_present_value / enterprise_value * 100
    ok = share_pct <= warning_threshold_pct
    return {
        "check": "terminal_value_share",
        "ok": ok,
        "value_pct": share_pct,
        "message": "Terminal value share is within threshold."
        if ok
        else "Terminal value drives most enterprise value; sensitivity is high.",
    }


def growth_vs_gdp_check(
    *,
    terminal_growth_pct: float,
    nominal_gdp_growth_pct: float,
    tolerance_pct: float = 0.5,
) -> dict[str, str | bool | float]:
    ok = terminal_growth_pct <= nominal_gdp_growth_pct + tolerance_pct
    return {
        "check": "growth_vs_gdp",
        "ok": ok,
        "spread_pct": terminal_growth_pct - nominal_gdp_growth_pct,
        "message": "Terminal growth is not materially above nominal GDP."
        if ok
        else "Terminal growth is materially above nominal GDP.",
    }


def peer_outlier_check(
    *,
    selected_multiple: float,
    peer_min_multiple: float,
    peer_max_multiple: float,
) -> dict[str, str | bool]:
    ok = peer_min_multiple <= selected_multiple <= peer_max_multiple
    return {
        "check": "peer_outlier",
        "ok": ok,
        "message": "Selected multiple sits within the peer range."
        if ok
        else "Selected multiple sits outside the peer range.",
    }
