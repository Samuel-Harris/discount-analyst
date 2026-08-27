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


def _distribution(**updates: object) -> IntrinsicValueDistribution:
    data: dict[str, object] = {
        "currency": "GBP",
        "current_share_price": 10.0,
        "expected_intrinsic_value": 13.0,
        "p10_intrinsic_value": 8.0,
        "p25_intrinsic_value": 11.0,
        "p50_intrinsic_value": 13.0,
        "p75_intrinsic_value": 16.0,
        "p90_intrinsic_value": 20.0,
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
    expected: float,
    methods: list[ValuationMethodResult],
    p10: float = 8.0,
    p90: float = 20.0,
) -> AppraiserOutput:
    return AppraiserOutput(
        ticker="TST",
        company_name="Test plc",
        valuation_date="2026-05-31",
        summary="Summary.",
        valuation_distribution=_distribution(
            expected_intrinsic_value=expected,
            p10_intrinsic_value=p10,
            p90_intrinsic_value=p90,
        ),
        methods=methods,
        key_value_drivers=["Driver"],
        downside_risks_to_value=["Risk"],
        upside_drivers_to_value=["Upside"],
        data_quality="Medium",
        caveats=["Caveat"],
        shares_outstanding=1_000_000.0,
        share_count_source="filing",
        quoted_price_unit="major",
    )


def test_appraiser_output_accepts_weight_blend() -> None:
    output = _output(
        expected=13.0,
        methods=[
            _method(
                method=ValuationMethod.SCENARIO_WEIGHTING,
                role="primary",
                value=10.0,
                weight_pct=70.0,
            ),
            _method(
                method=ValuationMethod.COMPARABLE_MULTIPLES,
                role="cross_check",
                value=20.0,
                weight_pct=30.0,
            ),
        ],
    )

    assert output.valuation_distribution.expected_intrinsic_value == 13.0


def test_appraiser_output_rejects_expected_equal_to_primary_only() -> None:
    with pytest.raises(ValidationError, match="weight-blend"):
        _output(
            expected=10.0,
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
            expected=16.0,
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
            expected=10.0,
            methods=[
                _method(
                    method=ValuationMethod.SCENARIO_WEIGHTING,
                    role="primary",
                    value=10.0,
                    weight_pct=100.0,
                )
            ],
        )


def test_mock_appraiser_output_expected_equals_blend() -> None:
    output = mock_appraiser_output(mock_surveyor_candidate(ticker="ABC.L"))
    blend = sum(
        method.value_per_share * method.weight_pct / 100.0 for method in output.methods
    )
    assert output.valuation_distribution.expected_intrinsic_value == blend
