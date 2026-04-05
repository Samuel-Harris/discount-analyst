"""Unit tests for ``sentinel_proceeds_to_valuation``."""

import pytest

from discount_analyst.agents.sentinel.schema import (
    EvaluationReport,
    OverallRedFlagVerdict,
    QuestionAssessment,
    RedFlagScreen,
    ThesisVerdict,
    sentinel_proceeds_to_valuation,
)


def _evaluation(
    *,
    thesis_verdict: ThesisVerdict,
    red_flag: OverallRedFlagVerdict = OverallRedFlagVerdict.CLEAR,
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


@pytest.mark.parametrize(
    ("thesis_verdict", "red_flag", "proceeds"),
    [
        (ThesisVerdict.INTACT_PROCEED_TO_VALUATION, OverallRedFlagVerdict.CLEAR, True),
        (ThesisVerdict.INTACT_WITH_RESERVATIONS, OverallRedFlagVerdict.CLEAR, True),
        (ThesisVerdict.WEAKENED_DO_NOT_PROCEED, OverallRedFlagVerdict.CLEAR, False),
        (ThesisVerdict.BROKEN_DO_NOT_PROCEED, OverallRedFlagVerdict.CLEAR, False),
        (
            ThesisVerdict.INTACT_PROCEED_TO_VALUATION,
            OverallRedFlagVerdict.SERIOUS_CONCERN,
            False,
        ),
        (
            ThesisVerdict.BROKEN_DO_NOT_PROCEED,
            OverallRedFlagVerdict.SERIOUS_CONCERN,
            False,
        ),
        (
            ThesisVerdict.INTACT_PROCEED_TO_VALUATION,
            OverallRedFlagVerdict.MONITOR,
            True,
        ),
        (
            ThesisVerdict.WEAKENED_DO_NOT_PROCEED,
            OverallRedFlagVerdict.MONITOR,
            False,
        ),
        (
            ThesisVerdict.WEAKENED_DO_NOT_PROCEED,
            OverallRedFlagVerdict.SERIOUS_CONCERN,
            False,
        ),
    ],
)
def test_sentinel_proceeds_to_valuation(
    thesis_verdict: ThesisVerdict,
    red_flag: OverallRedFlagVerdict,
    proceeds: bool,
) -> None:
    ev = _evaluation(thesis_verdict=thesis_verdict, red_flag=red_flag)
    assert sentinel_proceeds_to_valuation(ev) is proceeds
