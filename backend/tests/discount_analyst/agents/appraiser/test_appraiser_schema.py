"""Tests for method-agnostic Appraiser output validation."""

import pytest
from pydantic import ValidationError

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
        "expected_intrinsic_value": 14.0,
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
) -> ValuationMethodResult:
    return ValuationMethodResult.model_validate(
        {
            "method": method,
            "role": role,
            "value_per_share": value,
            "low_value_per_share": value * 0.8,
            "high_value_per_share": value * 1.2,
            "weight_pct": 50.0,
            "key_assumptions": ["Assumption"],
            "evidence_summary": ["Evidence"],
            "sanity_checks": ["Check"],
            "limitations": ["Limitation"],
        }
    )


def test_appraiser_output_accepts_primary_and_cross_check() -> None:
    output = AppraiserOutput(
        ticker="TST",
        company_name="Test plc",
        valuation_date="2026-05-31",
        summary="Summary.",
        valuation_distribution=_distribution(),
        methods=[
            _method(
                method=ValuationMethod.SCENARIO_WEIGHTING,
                role="primary",
                value=14.0,
            ),
            _method(
                method=ValuationMethod.COMPARABLE_MULTIPLES,
                role="cross_check",
                value=13.0,
            ),
        ],
        key_value_drivers=["Driver"],
        downside_risks_to_value=["Risk"],
        upside_drivers_to_value=["Upside"],
        data_quality="Medium",
        caveats=["Caveat"],
    )

    assert output.valuation_distribution.expected_intrinsic_value == 14.0


def test_distribution_rejects_non_monotonic_percentiles() -> None:
    with pytest.raises(ValidationError, match="monotonic"):
        _distribution(p25_intrinsic_value=21.0)


def test_distribution_rejects_expected_value_outside_range() -> None:
    with pytest.raises(ValidationError, match="expected_intrinsic_value"):
        _distribution(expected_intrinsic_value=25.0)


def test_appraiser_output_requires_cross_check() -> None:
    with pytest.raises(ValidationError, match="cross-check"):
        AppraiserOutput(
            ticker="TST",
            company_name="Test plc",
            valuation_date="2026-05-31",
            summary="Summary.",
            valuation_distribution=_distribution(),
            methods=[
                _method(
                    method=ValuationMethod.SCENARIO_WEIGHTING,
                    role="primary",
                    value=14.0,
                )
            ],
            data_quality="Medium",
        )
