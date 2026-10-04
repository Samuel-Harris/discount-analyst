"""Tests for code-derived Sentinel thesis verdicts and question-count checks."""

import pytest
from pydantic import ValidationError

from discount_analyst.agents.sentinel.derive_thesis_verdict import (
    SentinelQuestionCountError,
    derive_thesis_verdict,
    finalise_sentinel_evaluation,
)
from discount_analyst.agents.sentinel.schema import (
    EvaluationReport,
    OverallRedFlagVerdict,
    QuestionAssessment,
    RedFlagScreen,
    ThesisVerdict,
    stored_evaluation_report,
)
from discount_analyst.agents.strategist.schema import MispricingThesis


def _red_flags() -> RedFlagScreen:
    return RedFlagScreen(
        governance_concerns="",
        balance_sheet_stress="",
        customer_or_supplier_concentration="",
        accounting_quality="",
        related_party_transactions="",
        litigation_or_regulatory_risk="",
        overall_red_flag_verdict=OverallRedFlagVerdict.CLEAR,
    )


def _assessment(
    *,
    verdict: str,
    confidence: str,
    gap_kind: str,
    question: str = "Q",
) -> QuestionAssessment:
    return QuestionAssessment(
        question=question,
        evidence="E",
        verdict=verdict,  # type: ignore[arg-type]
        confidence=confidence,  # type: ignore[arg-type]
        gap_kind=gap_kind,  # type: ignore[arg-type]
    )


def _evaluation(*assessments: QuestionAssessment) -> EvaluationReport:
    return EvaluationReport(
        ticker="TST",
        company_name="Test Co",
        question_assessments=list(assessments),
        red_flag_screen=_red_flags(),
        thesis_verdict=ThesisVerdict.INTACT_PROCEED_TO_VALUATION,
        verdict_rationale="Stored rationale.",
        material_data_gaps="",
        caveats=[],
    )


def _thesis(*questions: str) -> MispricingThesis:
    return MispricingThesis(
        ticker="TST",
        company_name="Test Co",
        mispricing_type="t",
        market_belief="m",
        mispricing_argument="a",
        resolution_mechanism="r",
        falsification_conditions=["a", "b", "c"],
        thesis_risks=["x"],
        evaluation_questions=list(questions),
        permanent_loss_scenarios=["p1", "p2"],
        conviction_level="Medium",
        thesis_direction="undervalued",
    )


def test_all_calendar_weakens_is_intact_with_reservations_and_proceeds() -> None:
    evaluation = _evaluation(
        _assessment(
            verdict="Weakens thesis",
            confidence="High",
            gap_kind="calendar",
            question="FY26",
        ),
        _assessment(
            verdict="Supports thesis",
            confidence="High",
            gap_kind="calendar",
            question="Update",
        ),
    )
    derived = derive_thesis_verdict(evaluation)
    assert derived is ThesisVerdict.INTACT_WITH_RESERVATIONS
    assert evaluation.thesis_verdict is ThesisVerdict.INTACT_PROCEED_TO_VALUATION


def test_weakens_never_disclosed_is_rejected() -> None:
    with pytest.raises(ValidationError, match="never_disclosed"):
        _assessment(
            verdict="Weakens thesis",
            confidence="High",
            gap_kind="never_disclosed",
        )


def test_stored_weakens_never_disclosed_still_loads() -> None:
    report = stored_evaluation_report(
        {
            "ticker": "TST",
            "company_name": "Test Co",
            "question_assessments": [
                {
                    "question": "Q",
                    "evidence": "E",
                    "verdict": "Weakens thesis",
                    "confidence": "High",
                    "gap_kind": "never_disclosed",
                }
            ],
            "red_flag_screen": {
                "governance_concerns": "",
                "balance_sheet_stress": "",
                "customer_or_supplier_concentration": "",
                "accounting_quality": "",
                "related_party_transactions": "",
                "litigation_or_regulatory_risk": "",
                "overall_red_flag_verdict": "Clear",
            },
            "thesis_verdict": ThesisVerdict.INTACT_PROCEED_TO_VALUATION.value,
            "verdict_rationale": "Stored rationale.",
            "material_data_gaps": "",
            "caveats": [],
        }
    )
    assert report.question_assessments[0].gap_kind == "never_disclosed"
    assert report.thesis_verdict is ThesisVerdict.INTACT_PROCEED_TO_VALUATION


def test_weakens_calendar_is_allowed() -> None:
    assessment = _assessment(
        verdict="Weakens thesis",
        confidence="High",
        gap_kind="calendar",
    )
    assert assessment.gap_kind == "calendar"


def test_constructed_never_disclosed_weakens_stays_a_reservation() -> None:
    assessment = QuestionAssessment.model_construct(
        question="Q",
        evidence="E",
        verdict="Weakens thesis",
        confidence="High",
        gap_kind="never_disclosed",
    )
    evaluation = EvaluationReport.model_construct(
        ticker="TST",
        company_name="Test Co",
        question_assessments=[assessment],
        red_flag_screen=_red_flags(),
        thesis_verdict=ThesisVerdict.INTACT_PROCEED_TO_VALUATION,
        verdict_rationale="Stored rationale.",
        material_data_gaps="",
        caveats=[],
    )
    assert derive_thesis_verdict(evaluation) is ThesisVerdict.INTACT_WITH_RESERVATIONS


def test_printed_weakens_still_weakened() -> None:
    evaluation = _evaluation(
        _assessment(
            verdict="Weakens thesis",
            confidence="Medium",
            gap_kind="none",
        )
    )
    derived = derive_thesis_verdict(evaluation)
    assert derived is ThesisVerdict.WEAKENED_DO_NOT_PROCEED


def test_majority_low_printed_without_adverse_is_not_unproven() -> None:
    evaluation = _evaluation(
        _assessment(verdict="Supports thesis", confidence="Low", gap_kind="none"),
        _assessment(verdict="Neutral", confidence="Low", gap_kind="never_disclosed"),
        _assessment(verdict="Supports thesis", confidence="High", gap_kind="none"),
    )
    derived = derive_thesis_verdict(evaluation)
    assert derived is ThesisVerdict.INTACT_WITH_RESERVATIONS


def test_low_confidence_break_is_unproven_not_broken() -> None:
    evaluation = _evaluation(
        _assessment(verdict="Breaks thesis", confidence="Low", gap_kind="none"),
        _assessment(verdict="Supports thesis", confidence="High", gap_kind="none"),
    )
    assert derive_thesis_verdict(evaluation) is ThesisVerdict.UNPROVEN_DO_NOT_PROCEED


def test_finalise_overwrites_verdict_and_enforces_question_count() -> None:
    evaluation = _evaluation(
        _assessment(
            verdict="Weakens thesis",
            confidence="High",
            gap_kind="calendar",
            question="q1",
        ),
        _assessment(
            verdict="Supports thesis",
            confidence="High",
            gap_kind="none",
            question="q2",
        ),
        _assessment(
            verdict="Neutral",
            confidence="High",
            gap_kind="none",
            question="q3",
        ),
    )
    thesis = _thesis("q1", "q2", "q3")
    final = finalise_sentinel_evaluation(evaluation, thesis)
    assert final.thesis_verdict is ThesisVerdict.INTACT_WITH_RESERVATIONS
    assert evaluation.thesis_verdict is ThesisVerdict.INTACT_PROCEED_TO_VALUATION


def test_finalise_rejects_question_count_mismatch() -> None:
    evaluation = _evaluation(
        _assessment(verdict="Supports thesis", confidence="High", gap_kind="none")
    )
    thesis = _thesis("q1", "q2", "q3")
    with pytest.raises(SentinelQuestionCountError, match="3 evaluation questions"):
        finalise_sentinel_evaluation(evaluation, thesis)
