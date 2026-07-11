"""Tests for optional valuation toolkit helpers."""

from dataclasses import dataclass
from math import isclose
from typing import cast

import pytest

from discount_analyst.domain.valuation.toolkit.dcf import dcf_value_per_share
from discount_analyst.domain.valuation.toolkit.multiples import peer_multiple_valuation
from discount_analyst.domain.valuation.toolkit.sanity_checks import (
    expected_value_range_check,
    monotonic_percentile_check,
)
from discount_analyst.domain.valuation.toolkit.scenarios import (
    combine_scenarios_to_distribution,
)

REL_TOL = 1e-6


@dataclass(frozen=True)
class DcfScenario:
    id: str
    revenue: float
    revenue_growth_pct: float
    ebit_margin_pct: float
    tax_rate_pct: float
    depreciation_amortisation_pct: float
    capex_pct: float
    change_working_capital_pct: float
    years: int
    discount_rate_pct: float
    terminal_growth_pct: float
    net_debt: float
    shares_outstanding: float
    expected_value_per_share: float
    expected_enterprise_value: float
    expected_equity_value: float


DCF_SCENARIOS = [
    DcfScenario(
        id="Greggs plc.",
        revenue=2_014_400_000,
        revenue_growth_pct=8.0,
        ebit_margin_pct=9.7,
        tax_rate_pct=25.0,
        depreciation_amortisation_pct=5.0,
        capex_pct=7.5,
        change_working_capital_pct=1.0,
        years=7,
        discount_rate_pct=12.34,
        terminal_growth_pct=2.5,
        net_debt=2_500_000,
        shares_outstanding=101_775_428,
        expected_value_per_share=12.91211590179845,
        expected_enterprise_value=1_316_636_122.2911432,
        expected_equity_value=1_314_136_122.2911432,
    ),
    DcfScenario(
        id="Alphabet Inc.",
        revenue=350_018_000_000,
        revenue_growth_pct=10.0,
        ebit_margin_pct=32.1,
        tax_rate_pct=16.4,
        depreciation_amortisation_pct=3.6,
        capex_pct=15.0,
        change_working_capital_pct=1.0,
        years=10,
        discount_rate_pct=8.0,
        terminal_growth_pct=3.0,
        net_debt=-81_591_000_000,
        shares_outstanding=12_090_000_000,
        expected_value_per_share=165.90456951294698,
        expected_enterprise_value=1_924_195_245_411.529,
        expected_equity_value=2_005_786_245_411.529,
    ),
    DcfScenario(
        id="HSBC Holdings plc.",
        revenue=69_072_000_000,
        revenue_growth_pct=3.6,
        ebit_margin_pct=46.7,
        tax_rate_pct=16.4,
        depreciation_amortisation_pct=1.0,
        capex_pct=2.0,
        change_working_capital_pct=0.5,
        years=5,
        discount_rate_pct=6.575,
        terminal_growth_pct=2.5,
        net_debt=-116_660_000_000,
        shares_outstanding=17_730_000_000,
        expected_value_per_share=45.730803435997544,
        expected_enterprise_value=694_147_144_920.2365,
        expected_equity_value=810_807_144_920.2365,
    ),
    DcfScenario(
        id="Grainger plc",
        revenue=284_600_000,
        revenue_growth_pct=7.4,
        ebit_margin_pct=44.4,
        tax_rate_pct=0.0,
        depreciation_amortisation_pct=1.0,
        capex_pct=2.0,
        change_working_capital_pct=0.5,
        years=5,
        discount_rate_pct=9.738,
        terminal_growth_pct=3.0,
        net_debt=1_419_000_000,
        shares_outstanding=741_550_000,
        expected_value_per_share=1.1513541472107254,
        expected_enterprise_value=2_272_786_667.8641133,
        expected_equity_value=853_786_667.8641133,
    ),
    DcfScenario(
        id="Tesco plc",
        revenue=69_916_000_000,
        revenue_growth_pct=2.5,
        ebit_margin_pct=4.0,
        tax_rate_pct=25.0,
        depreciation_amortisation_pct=1.9,
        capex_pct=2.0,
        change_working_capital_pct=0.5,
        years=6,
        discount_rate_pct=7.372,
        terminal_growth_pct=2.0,
        net_debt=10_040_000_000,
        shares_outstanding=6_480_000_000,
        expected_value_per_share=4.522109139943345,
        expected_enterprise_value=39_343_267_226.83288,
        expected_equity_value=29_303_267_226.83288,
    ),
]


def test_dcf_value_per_share_returns_json_serialisable_result() -> None:
    result = dcf_value_per_share(
        revenue=100.0,
        revenue_growth_pct=5.0,
        ebit_margin_pct=20.0,
        tax_rate_pct=25.0,
        depreciation_amortisation_pct=3.0,
        capex_pct=4.0,
        change_working_capital_pct=1.0,
        years=3,
        discount_rate_pct=10.0,
        terminal_growth_pct=2.0,
        net_debt=10.0,
        shares_outstanding=10.0,
    )

    assert isclose(cast(float, result["value_per_share"]), 18.288662, rel_tol=REL_TOL)
    assert len(cast(list[dict[str, float]], result["projection"])) == 3


@pytest.mark.parametrize(
    "scenario",
    [pytest.param(scenario, id=scenario.id) for scenario in DCF_SCENARIOS],
)
def test_dcf_value_per_share_matches_ported_real_world_scenarios(
    scenario: DcfScenario,
) -> None:
    result = dcf_value_per_share(
        revenue=scenario.revenue,
        revenue_growth_pct=scenario.revenue_growth_pct,
        ebit_margin_pct=scenario.ebit_margin_pct,
        tax_rate_pct=scenario.tax_rate_pct,
        depreciation_amortisation_pct=scenario.depreciation_amortisation_pct,
        capex_pct=scenario.capex_pct,
        change_working_capital_pct=scenario.change_working_capital_pct,
        years=scenario.years,
        discount_rate_pct=scenario.discount_rate_pct,
        terminal_growth_pct=scenario.terminal_growth_pct,
        net_debt=scenario.net_debt,
        shares_outstanding=scenario.shares_outstanding,
    )

    assert isclose(
        cast(float, result["value_per_share"]),
        scenario.expected_value_per_share,
        rel_tol=REL_TOL,
    )
    assert isclose(
        cast(float, result["enterprise_value"]),
        scenario.expected_enterprise_value,
        rel_tol=REL_TOL,
    )
    assert isclose(
        cast(float, result["equity_value"]),
        scenario.expected_equity_value,
        rel_tol=REL_TOL,
    )
    assert len(cast(list[dict[str, float]], result["projection"])) == scenario.years


def test_peer_multiple_valuation_uses_median_when_no_selected_multiple() -> None:
    result = peer_multiple_valuation(
        peer_multiples=[7.0, 8.0, 9.0],
        target_financial_metric=20.0,
        net_debt=10.0,
        shares_outstanding=10.0,
    )

    assert result["selected_multiple"] == 8.0
    assert result["value_per_share"] == 15.0


def test_combine_scenarios_to_distribution_returns_percentiles() -> None:
    distribution = combine_scenarios_to_distribution(
        scenarios=[
            {"name": "bear", "value_per_share": 8.0, "probability_pct": 25.0},
            {"name": "base", "value_per_share": 12.0, "probability_pct": 50.0},
            {"name": "bull", "value_per_share": 20.0, "probability_pct": 25.0},
        ],
        current_share_price=10.0,
        currency="GBP",
    )

    assert distribution["expected_intrinsic_value"] == 13.0
    assert distribution["p10_intrinsic_value"] == 8.0
    assert distribution["p50_intrinsic_value"] == 12.0
    assert distribution["p90_intrinsic_value"] == 20.0


def test_sanity_checks_report_failures() -> None:
    assert monotonic_percentile_check(p10=1, p25=3, p50=2, p75=4, p90=5)["ok"] is False
    assert expected_value_range_check(expected_value=6, p10=1, p90=5)["ok"] is False
