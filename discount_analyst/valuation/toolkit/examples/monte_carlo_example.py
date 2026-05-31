"""Tiny Monte Carlo-style example producing a scenario distribution."""

from random import Random

from discount_analyst.valuation.toolkit.scenarios import (
    combine_scenarios_to_distribution,
)


if __name__ == "__main__":
    rng = Random(7)
    scenarios = [
        {
            "name": f"draw_{i}",
            "value_per_share": rng.uniform(8.0, 18.0),
            "probability_pct": 1.0,
        }
        for i in range(100)
    ]
    distribution = combine_scenarios_to_distribution(
        scenarios=scenarios,
        current_share_price=10.0,
        currency="GBP",
        distribution_method="simple_monte_carlo_draws",
        distribution_reasoning="Illustrative equal-weight simulation draws.",
    )
    print(distribution)
