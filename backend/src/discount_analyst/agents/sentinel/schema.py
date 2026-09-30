from collections.abc import Mapping
from enum import StrEnum
from typing import Any, Literal, cast

from pydantic import BaseModel, Field, ValidationError, model_validator


class ThesisVerdict(StrEnum):
    """Canonical thesis verdict strings (single source for schema, prompts, and labels)."""

    INTACT_PROCEED_TO_VALUATION = "Thesis intact — proceed to valuation"
    INTACT_WITH_RESERVATIONS = (
        "Thesis intact with reservations — proceed with noted caveats"
    )
    WEAKENED_DO_NOT_PROCEED = "Thesis weakened — do not proceed"
    UNPROVEN_DO_NOT_PROCEED = "Thesis unproven — do not proceed"
    BROKEN_DO_NOT_PROCEED = "Thesis broken — do not proceed"


class OverallRedFlagVerdict(StrEnum):
    """Canonical red-flag screen verdicts (schema and prompts)."""

    CLEAR = "Clear"
    MONITOR = "Monitor"
    SERIOUS_CONCERN = "Serious concern"


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
    gap_kind: Literal["none", "calendar", "never_disclosed", "contradicted"] = Field(
        description=(
            "Why evidence is missing or adverse: none (printed evidence, no "
            "calendar wait), calendar (the next print is not yet due), "
            "never_disclosed (the company has not published the fact), or "
            "contradicted (printed evidence conflicts with the thesis)."
        )
    )

    @model_validator(mode="after")
    def reject_adverse_never_disclosed(self) -> "QuestionAssessment":
        if self.verdict in {"Weakens thesis", "Breaks thesis"} and (
            self.gap_kind == "never_disclosed"
        ):
            msg = "Weakens thesis or Breaks thesis cannot use gap_kind never_disclosed."
            raise ValueError(msg)
        return self


def stored_question_assessment(data: Mapping[str, Any]) -> QuestionAssessment:
    """Load a stored assessment. Rows from before the gap rule still load."""
    payload: dict[str, Any] = {
        "question": data["question"],
        "evidence": data["evidence"],
        "verdict": data["verdict"],
        "confidence": data["confidence"],
        "gap_kind": data["gap_kind"],
    }
    try:
        return QuestionAssessment.model_validate(payload)
    except ValidationError:
        return QuestionAssessment.model_construct(**payload)


class RedFlagScreen(BaseModel):
    """Thesis-agnostic permanent-loss and governance screens."""

    governance_concerns: str
    balance_sheet_stress: str
    customer_or_supplier_concentration: str
    accounting_quality: str
    related_party_transactions: str
    litigation_or_regulatory_risk: str
    overall_red_flag_verdict: OverallRedFlagVerdict


class EvaluationReport(BaseModel):
    """Sentinel output: thesis evaluation, red flags, and thesis verdict (label only)."""

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
            "been resolved. If these gaps prevent a confident thesis verdict, "
            "state that explicitly."
        )
    )
    caveats: list[str] = Field(
        description=(
            "Specific conditions or uncertainties Appraiser and Curator should "
            "be aware of. thesis_verdict is derived in code and is an evidence "
            "label, not a stop."
        )
    )


def stored_evaluation_report(data: Mapping[str, Any]) -> EvaluationReport:
    """Load a stored Sentinel report, including pre-gap-rule assessments."""
    try:
        return EvaluationReport.model_validate(dict(data))
    except ValidationError:
        assessments: list[QuestionAssessment] = []
        for item in cast(list[object], data["question_assessments"]):
            if isinstance(item, QuestionAssessment):
                assessments.append(item)
            elif isinstance(item, dict):
                assessments.append(
                    stored_question_assessment(cast(dict[str, Any], item))
                )
            else:
                msg = "A stored question assessment must be an object."
                raise TypeError(msg)
        red_flag = data["red_flag_screen"]
        thesis_verdict = data["thesis_verdict"]
        return EvaluationReport.model_construct(
            ticker=data["ticker"],
            company_name=data["company_name"],
            question_assessments=assessments,
            red_flag_screen=(
                red_flag
                if isinstance(red_flag, RedFlagScreen)
                else RedFlagScreen.model_validate(red_flag)
            ),
            thesis_verdict=(
                thesis_verdict
                if isinstance(thesis_verdict, ThesisVerdict)
                else ThesisVerdict(thesis_verdict)
            ),
            verdict_rationale=data["verdict_rationale"],
            material_data_gaps=data["material_data_gaps"],
            caveats=list(data["caveats"]),
        )
