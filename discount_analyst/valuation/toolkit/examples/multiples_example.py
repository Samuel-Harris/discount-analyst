"""Example terminal script using peer multiple helpers."""

from discount_analyst.valuation.toolkit.multiples import peer_multiple_valuation


if __name__ == "__main__":
    result = peer_multiple_valuation(
        peer_multiples=[7.5, 8.1, 9.0, 10.2, 12.0],
        target_financial_metric=25_000_000,
        net_debt=10_000_000,
        shares_outstanding=50_000_000,
    )
    print(result["value_per_share"])
