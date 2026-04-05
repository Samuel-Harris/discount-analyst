"""Tests for programmatic verdict builders."""

import pytest

from discount_analyst.agents.arbiter.schema import (
    ArbiterDecision,
    ArbiterRationale,
    MarginOfSafetyAssessment,
)
from discount_analyst.agents.sentinel.schema import (
    EvaluationReport,
    OverallRedFlagVerdict,
    QuestionAssessment,
    RedFlagScreen,
    ThesisVerdict,
)
from discount_analyst.agents.strategist.schema import MispricingThesis
from discount_analyst.pipeline.builders import (
    build_sentinel_rejection,
    verdict_from_decision,
)
from discount_analyst.pipeline.schema import SentinelRejection
from discount_analyst.rating import InvestmentRating


def _evaluation(
    *,
    thesis_verdict: ThesisVerdict,
    red_flag: OverallRedFlagVerdict,
) -> EvaluationReport:
    return EvaluationReport(
        ticker="TST",
        company_name="Test Co",
        question_assessments=[
            QuestionAssessment(
                question="Q1",
                evidence="E",
                verdict="Supports thesis",
                confidence="High",
            )
        ],
        red_flag_screen=RedFlagScreen(
            governance_concerns="",
            balance_sheet_stress="",
            customer_or_supplier_concentration="",
            accounting_quality="",
            related_party_transactions="",
            litigation_or_regulatory_risk="",
            overall_red_flag_verdict=red_flag,
        ),
        thesis_verdict=thesis_verdict,
        verdict_rationale="",
        material_data_gaps="",
        caveats=[],
    )


def _thesis() -> MispricingThesis:
    return MispricingThesis(
        ticker="TST",
        company_name="Test Co",
        mispricing_type="t",
        market_belief="m",
        mispricing_argument="a",
        resolution_mechanism="r",
        falsification_conditions=["a", "b", "c"],
        thesis_risks=["x"],
        evaluation_questions=["q1", "q2", "q3", "q4", "q5"],
        permanent_loss_scenarios=["p1", "p2"],
        conviction_level="Medium",
    )


@pytest.mark.parametrize(
    ("thesis_v", "red_flag", "expected_rating"),
    [
        (
            ThesisVerdict.BROKEN_DO_NOT_PROCEED,
            OverallRedFlagVerdict.CLEAR,
            InvestmentRating.STRONG_SELL,
        ),
        (
            ThesisVerdict.WEAKENED_DO_NOT_PROCEED,
            OverallRedFlagVerdict.CLEAR,
            InvestmentRating.SELL,
        ),
        (
            ThesisVerdict.INTACT_PROCEED_TO_VALUATION,
            OverallRedFlagVerdict.SERIOUS_CONCERN,
            InvestmentRating.STRONG_SELL,
        ),
        (
            ThesisVerdict.WEAKENED_DO_NOT_PROCEED,
            OverallRedFlagVerdict.MONITOR,
            InvestmentRating.SELL,
        ),
    ],
)
def test_build_sentinel_rejection_rating_rules(
    thesis_v: ThesisVerdict,
    red_flag: OverallRedFlagVerdict,
    expected_rating: InvestmentRating,
) -> None:
    ev = _evaluation(thesis_verdict=thesis_v, red_flag=red_flag)
    sr = build_sentinel_rejection(
        ev,
        _thesis(),
        is_existing_position=False,
        decision_date="2026-04-05",
    )
    assert sr.rating == expected_rating


def test_build_sentinel_rejection_recommended_action_new_vs_held() -> None:
    ev = _evaluation(
        thesis_verdict=ThesisVerdict.WEAKENED_DO_NOT_PROCEED,
        red_flag=OverallRedFlagVerdict.CLEAR,
    )
    new_cand = build_sentinel_rejection(
        ev, _thesis(), is_existing_position=False, decision_date="d"
    )
    held = build_sentinel_rejection(
        ev, _thesis(), is_existing_position=True, decision_date="d"
    )
    assert new_cand.recommended_action == "Do not initiate."
    assert held.recommended_action == "Exit the position."


def test_build_sentinel_rejection_ticker_mismatch_raises() -> None:
    ev = _evaluation(
        thesis_verdict=ThesisVerdict.WEAKENED_DO_NOT_PROCEED,
        red_flag=OverallRedFlagVerdict.CLEAR,
    )
    thesis = _thesis().model_copy(update={"ticker": "OTHER"})
    with pytest.raises(ValueError, match="ticker"):
        build_sentinel_rejection(
            ev,
            thesis,
            is_existing_position=False,
            decision_date="d",
        )


def test_verdict_from_decision_hoists_sentinel_fields() -> None:
    sr = SentinelRejection(
        ticker="T",
        company_name="C",
        decision_date="2026-04-05",
        is_existing_position=True,
        rating=InvestmentRating.SELL,
        recommended_action="Exit the position.",
        rejection_reason="Because.",
    )
    v = verdict_from_decision(sr)
    assert v.ticker == sr.ticker
    assert v.company_name == sr.company_name
    assert v.decision_date == sr.decision_date
    assert v.is_existing_position == sr.is_existing_position
    assert v.rating == sr.rating
    assert v.recommended_action == sr.recommended_action
    assert v.decision is sr


def test_verdict_from_decision_hoists_arbiter_fields() -> None:
    ad = ArbiterDecision(
        ticker="T",
        company_name="C",
        decision_date="2026-04-05",
        is_existing_position=False,
        rating=InvestmentRating.BUY,
        recommended_action="Initiate.",
        conviction="Medium",
        margin_of_safety=MarginOfSafetyAssessment(
            current_price=10.0,
            bear_intrinsic_value=8.0,
            base_intrinsic_value=12.0,
            bull_intrinsic_value=15.0,
            margin_of_safety_base_pct=20.0,
            margin_of_safety_verdict=(
                "Moderate — meaningful upside but not exceptional"
            ),
        ),
        rationale=ArbiterRationale(
            primary_driver="x",
            supporting_factors=["a"],
            mitigating_factors=["b"],
            red_flag_disposition="c",
            data_gap_disposition="d",
        ),
        thesis_expiry_note="12-18 months",
    )
    v = verdict_from_decision(ad)
    assert v.rating == ad.rating
    assert v.recommended_action == ad.recommended_action
    assert v.decision is ad
