"""Tests for programmatic verdict builders."""

import pytest

from discount_analyst.adapters.simulation.mock_outputs import mock_surveyor_candidate
from discount_analyst.agents.sentinel.schema import (
    EvaluationReport,
    OverallRedFlagVerdict,
    QuestionAssessment,
    RedFlagScreen,
    ThesisVerdict,
)
from discount_analyst.agents.strategist.schema import MispricingThesis
from discount_analyst.application.decisions.builders import (
    build_data_quality_rejection,
    build_sentinel_rejection,
    verdict_from_decision,
)
from discount_analyst.domain.decisions.schema import (
    DataQualityRejection,
    RatingTableDecision,
    RatingTableRationale,
    SentinelRejection,
    Verdict,
)
from discount_analyst.domain.decisions.investment_rating import InvestmentRating
from discount_analyst.domain.decisions.margin_of_safety import MarginOfSafetyAssessment


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
                gap_kind="none",
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
        verdict_rationale="Printed evidence weakened the core claim.",
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


def test_build_data_quality_rejection_recommended_action() -> None:
    lane_context = mock_surveyor_candidate(ticker="BAD.L").to_lane_context()
    rejection = build_data_quality_rejection(
        lane_context,
        gate_failure_reason="Ticker mismatch.",
        is_existing_position=False,
        decision_date="2026-06-21",
    )
    assert rejection.rating == InvestmentRating.SELL
    assert rejection.recommended_action.startswith("Do not initiate")
    verdict = verdict_from_decision(rejection)
    assert isinstance(verdict.decision, DataQualityRejection)


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
    assert "Printed evidence weakened the core claim." in new_cand.rejection_reason
    assert "gap_kind tally:" in new_cand.rejection_reason


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
        decision_kind="sentinel_rejection",
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


def _rating_table_decision() -> RatingTableDecision:
    mos = MarginOfSafetyAssessment(
        current_price=10.0,
        expected_intrinsic_value=12.0,
        p10_intrinsic_value=8.0,
        p90_intrinsic_value=16.0,
    )
    return RatingTableDecision(
        decision_kind="rating_table",
        decision_rule_id="rating_table_v1",
        ticker="T",
        company_name="C",
        decision_date="2026-04-05",
        is_existing_position=False,
        rating=InvestmentRating.BUY,
        recommended_action="Initiate at half or quarter position (starter)",
        conviction="Medium",
        margin_of_safety=mos,
        rationale=RatingTableRationale(
            primary_driver="x",
            supporting_factors=[],
            mitigating_factors=[],
            red_flag_disposition="c",
            data_gap_disposition="d",
        ),
        thesis_expiry_note="12-18 months",
    )


def test_verdict_from_decision_hoists_rating_table_fields() -> None:
    rtd = _rating_table_decision()
    v = verdict_from_decision(rtd)
    assert v.rating == rtd.rating
    assert v.recommended_action == rtd.recommended_action
    assert v.decision is rtd


def test_verdict_json_round_trip_preserves_data_quality_rejection() -> None:
    lane_context = mock_surveyor_candidate(ticker="BAD.L").to_lane_context()
    rejection = build_data_quality_rejection(
        lane_context,
        gate_failure_reason="Ticker mismatch.",
        is_existing_position=False,
        decision_date="2026-06-21",
    )
    restored = Verdict.model_validate_json(
        verdict_from_decision(rejection).model_dump_json()
    )
    assert isinstance(restored.decision, DataQualityRejection)
    assert restored.decision.decision_kind == "data_quality_rejection"
    assert restored.decision.rejection_reason == "Ticker mismatch."


def test_verdict_json_round_trip_preserves_sentinel_rejection() -> None:
    ev = _evaluation(
        thesis_verdict=ThesisVerdict.WEAKENED_DO_NOT_PROCEED,
        red_flag=OverallRedFlagVerdict.CLEAR,
    )
    rejection = build_sentinel_rejection(
        ev, _thesis(), is_existing_position=False, decision_date="2026-04-05"
    )
    restored = Verdict.model_validate_json(
        verdict_from_decision(rejection).model_dump_json()
    )
    assert isinstance(restored.decision, SentinelRejection)
    assert restored.decision.decision_kind == "sentinel_rejection"


def test_verdict_json_round_trip_preserves_rating_table_decision() -> None:
    rtd = _rating_table_decision()
    restored = Verdict.model_validate_json(verdict_from_decision(rtd).model_dump_json())
    assert isinstance(restored.decision, RatingTableDecision)
    assert restored.decision.decision_kind == "rating_table"
    assert restored.decision.decision_rule_id == "rating_table_v1"
