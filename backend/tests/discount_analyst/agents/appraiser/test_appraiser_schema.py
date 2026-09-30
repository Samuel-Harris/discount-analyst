"""Tests for method-agnostic Appraiser output validation."""

import pytest
from pydantic import ValidationError

from discount_analyst.adapters.simulation.mock_outputs import (
    mock_appraiser_output,
    mock_surveyor_candidate,
)
from discount_analyst.agents.appraiser.schema import (
    AppraiserOutput,
    ValuationMethod,
    ValuationMethodResult,
)
from discount_analyst.domain.valuation.intrinsic_value_distribution import (
    IntrinsicValueDistribution,
)
from discount_analyst.domain.valuation.toolkit.scenarios import (
    weighted_expected_value,
    weighted_percentile,
)

_SCENARIOS: list[dict[str, float | str]] = [
    {"value_per_share": 8.0, "probability_pct": 20.0},
    {"value_per_share": 11.0, "probability_pct": 15.0},
    {"value_per_share": 13.0, "probability_pct": 30.0},
    {"value_per_share": 16.0, "probability_pct": 20.0},
    {"value_per_share": 20.0, "probability_pct": 15.0},
]
_SCENARIO_EXPECTED = weighted_expected_value(_SCENARIOS)


def _distribution(**updates: object) -> IntrinsicValueDistribution:
    data: dict[str, object] = {
        "currency": "GBP",
        "current_share_price": 10.0,
        "expected_intrinsic_value": _SCENARIO_EXPECTED,
        "p10_intrinsic_value": weighted_percentile(_SCENARIOS, 10),
        "p25_intrinsic_value": weighted_percentile(_SCENARIOS, 25),
        "p50_intrinsic_value": weighted_percentile(_SCENARIOS, 50),
        "p75_intrinsic_value": weighted_percentile(_SCENARIOS, 75),
        "p90_intrinsic_value": weighted_percentile(_SCENARIOS, 90),
        "scenarios": _SCENARIOS,
        "distribution_method": "scenario_weighting",
        "distribution_reasoning": "Weighted downside/base/upside scenarios.",
    }
    data.update(updates)
    return IntrinsicValueDistribution.model_validate(data)


def _method(
    *,
    method: ValuationMethod,
    role: str,
    value: float,
    weight_pct: float,
) -> ValuationMethodResult:
    return ValuationMethodResult.model_validate(
        {
            "method": method,
            "role": role,
            "value_per_share": value,
            "low_value_per_share": value * 0.8,
            "high_value_per_share": value * 1.2,
            "weight_pct": weight_pct,
            "key_assumptions": ["Assumption"],
            "evidence_summary": ["Evidence"],
            "sanity_checks": ["Check"],
            "limitations": ["Limitation"],
        }
    )


def _output(
    *,
    methods: list[ValuationMethodResult],
    shares_outstanding: float = 1_000_000.0,
) -> AppraiserOutput:
    return AppraiserOutput(
        ticker="TST",
        company_name="Test plc",
        valuation_date="2026-05-31",
        summary="Summary.",
        valuation_distribution=_distribution(),
        methods=methods,
        key_value_drivers=["Driver"],
        downside_risks_to_value=["Risk"],
        upside_drivers_to_value=["Upside"],
        data_quality="Medium",
        caveats=["Caveat"],
        shares_outstanding=shares_outstanding,
        share_count_source="filing",
        quoted_price_unit="major",
    )


def test_appraiser_output_accepts_weight_blend() -> None:
    output = _output(
        methods=[
            _method(
                method=ValuationMethod.SCENARIO_WEIGHTING,
                role="primary",
                value=10.0,
                weight_pct=60.0,
            ),
            _method(
                method=ValuationMethod.COMPARABLE_MULTIPLES,
                role="cross_check",
                value=18.375,
                weight_pct=40.0,
            ),
        ],
    )

    assert output.valuation_distribution.expected_intrinsic_value == _SCENARIO_EXPECTED


def test_appraiser_output_rejects_expected_equal_to_primary_only() -> None:
    with pytest.raises(ValidationError, match="weight-blend"):
        _output(
            methods=[
                _method(
                    method=ValuationMethod.SCENARIO_WEIGHTING,
                    role="primary",
                    value=10.0,
                    weight_pct=80.0,
                ),
                _method(
                    method=ValuationMethod.COMPARABLE_MULTIPLES,
                    role="cross_check",
                    value=20.0,
                    weight_pct=20.0,
                ),
            ],
        )


def test_appraiser_output_rejects_expected_off_by_more_than_half_percent() -> None:
    with pytest.raises(ValidationError, match="weight-blend"):
        _output(
            methods=[
                _method(
                    method=ValuationMethod.SCENARIO_WEIGHTING,
                    role="primary",
                    value=10.0,
                    weight_pct=60.0,
                ),
                _method(
                    method=ValuationMethod.COMPARABLE_MULTIPLES,
                    role="cross_check",
                    value=20.0,
                    weight_pct=40.0,
                ),
            ],
        )


def test_appraiser_output_rejects_missing_weight_pct() -> None:
    with pytest.raises(ValidationError):
        ValuationMethodResult.model_validate(
            {
                "method": ValuationMethod.SCENARIO_WEIGHTING,
                "role": "primary",
                "value_per_share": 10.0,
            }
        )


def test_appraiser_output_rejects_other_method() -> None:
    with pytest.raises(ValidationError):
        ValuationMethodResult.model_validate(
            {
                "method": "other",
                "role": "cross_check",
                "value_per_share": 10.0,
                "weight_pct": 30.0,
            }
        )


def test_distribution_rejects_non_monotonic_percentiles() -> None:
    with pytest.raises(ValidationError, match="monotonic"):
        _distribution(p25_intrinsic_value=21.0)


def test_distribution_rejects_expected_value_outside_range() -> None:
    with pytest.raises(ValidationError, match="expected_intrinsic_value"):
        _distribution(expected_intrinsic_value=25.0)


def test_appraiser_output_requires_cross_check() -> None:
    with pytest.raises(ValidationError, match="cross-check"):
        _output(
            methods=[
                _method(
                    method=ValuationMethod.SCENARIO_WEIGHTING,
                    role="primary",
                    value=10.0,
                    weight_pct=100.0,
                )
            ],
        )


def test_distribution_accepts_percentiles_that_match_scenarios() -> None:
    distribution = _distribution()
    assert distribution.p10_intrinsic_value == 8.0
    assert distribution.expected_intrinsic_value == _SCENARIO_EXPECTED


def test_distribution_rejects_percentile_outside_scenario_values() -> None:
    with pytest.raises(ValidationError, match="p10_intrinsic_value"):
        _distribution(p10_intrinsic_value=9.0)


def test_appraiser_output_rejects_share_count_below_100_000() -> None:
    with pytest.raises(ValidationError, match="shares_outstanding"):
        _output(
            shares_outstanding=260.92,
            methods=[
                _method(
                    method=ValuationMethod.SCENARIO_WEIGHTING,
                    role="primary",
                    value=10.0,
                    weight_pct=60.0,
                ),
                _method(
                    method=ValuationMethod.COMPARABLE_MULTIPLES,
                    role="cross_check",
                    value=18.375,
                    weight_pct=40.0,
                ),
            ],
        )


def test_appraiser_output_accepts_raw_share_count_at_100_000() -> None:
    output = _output(
        shares_outstanding=100_000,
        methods=[
            _method(
                method=ValuationMethod.SCENARIO_WEIGHTING,
                role="primary",
                value=10.0,
                weight_pct=60.0,
            ),
            _method(
                method=ValuationMethod.COMPARABLE_MULTIPLES,
                role="cross_check",
                value=18.375,
                weight_pct=40.0,
            ),
        ],
    )
    assert output.shares_outstanding == 100_000


def test_mock_appraiser_output_expected_equals_blend() -> None:
    output = mock_appraiser_output(mock_surveyor_candidate(ticker="ABC.L"))
    blend = sum(
        method.value_per_share * method.weight_pct / 100.0 for method in output.methods
    )
    assert abs(output.valuation_distribution.expected_intrinsic_value - blend) < 1e-9
