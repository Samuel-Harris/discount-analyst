from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class ThesisVerdict(StrEnum):
    """Canonical thesis verdict strings (single source for schema, prompts, and gate logic)."""

    INTACT_PROCEED_TO_VALUATION = "Thesis intact — proceed to valuation"
    INTACT_WITH_RESERVATIONS = (
        "Thesis intact with reservations — proceed with noted caveats"
    )
    WEAKENED_DO_NOT_PROCEED = "Thesis weakened — do not proceed"
    BROKEN_DO_NOT_PROCEED = "Thesis broken — do not proceed"


_THESIS_VERDICTS_PROCEED: frozenset[ThesisVerdict] = frozenset(
    {
        ThesisVerdict.INTACT_PROCEED_TO_VALUATION,
        ThesisVerdict.INTACT_WITH_RESERVATIONS,
    }
)


def sentinel_proceeds_to_valuation(thesis_verdict: ThesisVerdict) -> bool:
    """True iff ``thesis_verdict`` authorises the Appraiser / DCF stage."""

    return thesis_verdict in _THESIS_VERDICTS_PROCEED


class QuestionAssessment(BaseModel):
    """Assessment of one thesis evaluation question against the evidence base."""

    question: str
    evidence: str = Field(
        description="What the research shows in response to this question."
    )
    verdict: Literal["Supports thesis", "Neutral", "Weakens thesis", "Breaks thesis"]
    confidence: Literal["Low", "Medium", "High"] = Field(
        description="Confidence in this assessment given the available evidence."
    )


class RedFlagScreen(BaseModel):
    """Thesis-agnostic permanent-loss and governance screens."""

    governance_concerns: str
    balance_sheet_stress: str
    customer_or_supplier_concentration: str
    accounting_quality: str
    related_party_transactions: str
    litigation_or_regulatory_risk: str
    overall_red_flag_verdict: Literal["Clear", "Monitor", "Serious concern"]


class EvaluationReport(BaseModel):
    """Sentinel output: thesis evaluation, red flags, and thesis verdict (gate is derived)."""

    ticker: str
    company_name: str

    question_assessments: list[QuestionAssessment] = Field(
        description="One entry per evaluation_question from the MispricingThesis."
    )
    red_flag_screen: RedFlagScreen

    thesis_verdict: ThesisVerdict
    verdict_rationale: str = Field(
        description=(
            "The reasoning behind the thesis_verdict. Should directly reference "
            "the question assessments and red flag screen."
        )
    )
    material_data_gaps: str = Field(
        description=(
            "Any data gaps that are load-bearing for the thesis and have not "
            "been resolved. If these gaps prevent a confident recommendation, "
            "state that explicitly."
        )
    )
    caveats: list[str] = Field(
        description=(
            "Specific conditions or uncertainties the Appraiser and final "
            "decision agent should be aware of."
        )
    )
