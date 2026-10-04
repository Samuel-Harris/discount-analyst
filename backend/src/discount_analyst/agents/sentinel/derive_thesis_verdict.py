"""Derive Sentinel thesis_verdict from question assessments (code wins)."""

from discount_analyst.agents.sentinel.schema import EvaluationReport, ThesisVerdict
from discount_analyst.agents.strategist.schema import MispricingThesis

_PRINTED_WEAKENS_GAP_KINDS = frozenset({"none", "contradicted"})
_SOFT_GAP_KINDS = frozenset({"calendar", "never_disclosed"})
_BREAKS_THESIS = "Breaks thesis"
_WEAKENS_THESIS = "Weakens thesis"
_MEDIUM_OR_HIGH = frozenset({"Medium", "High"})


class SentinelQuestionCountError(ValueError):
    """Sentinel returned a different number of assessments than thesis questions."""


def derive_thesis_verdict(evaluation: EvaluationReport) -> ThesisVerdict:
    """Map question assessments to a thesis verdict.

    Does not rewrite ``evaluation.thesis_verdict``. Callers overwrite after a
    successful agent run, before persist. Stored rows are not re-derived on read.
    """

    assessments = evaluation.question_assessments
    if any(
        assessment.verdict == _BREAKS_THESIS
        and assessment.confidence in _MEDIUM_OR_HIGH
        for assessment in assessments
    ):
        return ThesisVerdict.BROKEN_DO_NOT_PROCEED
    if any(
        assessment.verdict == _WEAKENS_THESIS
        and assessment.gap_kind in _PRINTED_WEAKENS_GAP_KINDS
        for assessment in assessments
    ):
        return ThesisVerdict.WEAKENED_DO_NOT_PROCEED
    printed = [
        assessment
        for assessment in assessments
        if assessment.gap_kind not in _SOFT_GAP_KINDS
    ]
    if printed:
        low_count = sum(1 for assessment in printed if assessment.confidence == "Low")
        has_adverse = any(
            assessment.verdict in {_WEAKENS_THESIS, _BREAKS_THESIS}
            for assessment in assessments
        )
        if low_count * 2 >= len(printed) and has_adverse:
            return ThesisVerdict.UNPROVEN_DO_NOT_PROCEED
    if any(assessment.gap_kind in _SOFT_GAP_KINDS for assessment in assessments):
        return ThesisVerdict.INTACT_WITH_RESERVATIONS
    return ThesisVerdict.INTACT_PROCEED_TO_VALUATION


def finalise_sentinel_evaluation(
    evaluation: EvaluationReport,
    thesis: MispricingThesis,
) -> EvaluationReport:
    """Check question count, then overwrite thesis_verdict with the derived value."""

    expected = len(thesis.evaluation_questions)
    actual = len(evaluation.question_assessments)
    if actual != expected:
        msg = (
            f"Sentinel returned {actual} question assessments but the thesis "
            f"has {expected} evaluation questions."
        )
        raise SentinelQuestionCountError(msg)
    return evaluation.model_copy(
        update={"thesis_verdict": derive_thesis_verdict(evaluation)}
    )
