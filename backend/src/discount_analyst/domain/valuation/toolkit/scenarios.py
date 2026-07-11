"""Scenario weighting helpers for intrinsic-value distributions."""

from __future__ import annotations


def _normalise_probabilities(scenarios: list[dict[str, float | str]]) -> list[float]:
    probabilities = [float(s["probability_pct"]) for s in scenarios]
    total = sum(probabilities)
    if total <= 0:
        raise ValueError("Scenario probabilities must sum to a positive value.")
    return [p / total for p in probabilities]


def weighted_expected_value(scenarios: list[dict[str, float | str]]) -> float:
    if not scenarios:
        raise ValueError("scenarios must not be empty.")
    probabilities = _normalise_probabilities(scenarios)
    return sum(
        float(scenario["value_per_share"]) * probability
        for scenario, probability in zip(scenarios, probabilities, strict=True)
    )


def weighted_percentile(
    scenarios: list[dict[str, float | str]],
    percentile: float,
) -> float:
    if not 0 <= percentile <= 100:
        msg = f"percentile must be between 0 and 100, got {percentile}."
        raise ValueError(msg)
    probabilities = _normalise_probabilities(scenarios)
    ordered = sorted(
        zip(scenarios, probabilities, strict=True),
        key=lambda item: float(item[0]["value_per_share"]),
    )
    threshold = percentile / 100
    cumulative = 0.0
    for scenario, probability in ordered:
        cumulative += probability
        if cumulative >= threshold:
            return float(scenario["value_per_share"])
    return float(ordered[-1][0]["value_per_share"])


def combine_scenarios_to_distribution(
    *,
    scenarios: list[dict[str, float | str]],
    current_share_price: float,
    currency: str,
    distribution_method: str = "scenario_weighting",
    distribution_reasoning: str = "Weighted scenario distribution.",
) -> dict[str, float | str]:
    """Return the Appraiser distribution shape from scenario values."""
    if current_share_price <= 0:
        msg = f"current_share_price must be positive, got {current_share_price}."
        raise ValueError(msg)
    return {
        "currency": currency,
        "current_share_price": current_share_price,
        "expected_intrinsic_value": weighted_expected_value(scenarios),
        "p10_intrinsic_value": weighted_percentile(scenarios, 10),
        "p25_intrinsic_value": weighted_percentile(scenarios, 25),
        "p50_intrinsic_value": weighted_percentile(scenarios, 50),
        "p75_intrinsic_value": weighted_percentile(scenarios, 75),
        "p90_intrinsic_value": weighted_percentile(scenarios, 90),
        "distribution_method": distribution_method,
        "distribution_reasoning": distribution_reasoning,
    }
