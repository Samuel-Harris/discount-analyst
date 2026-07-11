from __future__ import annotations

from discount_analyst.agents.sentinel.schema import (
    EvaluationReport,
    OverallRedFlagVerdict,
    ThesisVerdict,
)
from discount_analyst.agents.strategist.schema import MispricingThesis
from discount_analyst.agents.surveyor.schema import SurveyorLaneContext
from discount_analyst.domain.decisions.rating_decision_table import (
    rating_from_table_inputs,
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


def build_sentinel_rejection(
    evaluation: EvaluationReport,
    thesis: MispricingThesis,
    *,
    is_existing_position: bool,
    decision_date: str,
) -> SentinelRejection:
    """Build a programmatic ``SentinelRejection`` from Sentinel evaluation + thesis."""
    if thesis.ticker.casefold() != evaluation.ticker.casefold():
        msg = (
            f"Thesis ticker {thesis.ticker!r} does not match evaluation "
            f"{evaluation.ticker!r}."
        )
        raise ValueError(msg)

    red_serious = (
        evaluation.red_flag_screen.overall_red_flag_verdict
        == OverallRedFlagVerdict.SERIOUS_CONCERN
    )
    thesis_broken = evaluation.thesis_verdict == ThesisVerdict.BROKEN_DO_NOT_PROCEED
    strong_sell = thesis_broken or red_serious
    rating = InvestmentRating.STRONG_SELL if strong_sell else InvestmentRating.SELL

    if is_existing_position:
        recommended_action = (
            "Exit immediately."
            if rating == InvestmentRating.STRONG_SELL
            else "Exit the position."
        )
    else:
        recommended_action = (
            "Avoid." if rating == InvestmentRating.STRONG_SELL else "Do not initiate."
        )

    reason_parts: list[str] = []
    if evaluation.thesis_verdict not in (
        ThesisVerdict.INTACT_PROCEED_TO_VALUATION,
        ThesisVerdict.INTACT_WITH_RESERVATIONS,
    ):
        reason_parts.append(f"Thesis verdict: {evaluation.thesis_verdict}.")
    if red_serious:
        reason_parts.append(
            f'Red-flag screen: overall verdict is "{OverallRedFlagVerdict.SERIOUS_CONCERN}".'
        )
    if not reason_parts:
        reason_parts.append(
            "Sentinel evaluation does not support proceeding to valuation."
        )
    rejection_reason = " ".join(reason_parts)

    return SentinelRejection(
        ticker=evaluation.ticker,
        company_name=evaluation.company_name,
        decision_date=decision_date,
        is_existing_position=is_existing_position,
        rating=rating,
        recommended_action=recommended_action,
        rejection_reason=rejection_reason,
    )


def build_data_quality_rejection(
    lane_context: SurveyorLaneContext,
    *,
    gate_failure_reason: str,
    is_existing_position: bool,
    decision_date: str,
) -> DataQualityRejection:
    """Build a programmatic ``DataQualityRejection`` from a failed candidate gate."""
    if is_existing_position:
        recommended_action = "Exit the position; data quality gate failed."
    else:
        recommended_action = "Do not initiate; data quality gate failed."
    return DataQualityRejection(
        ticker=lane_context.ticker,
        company_name=lane_context.company_name,
        decision_date=decision_date,
        is_existing_position=is_existing_position,
        rating=InvestmentRating.SELL,
        recommended_action=recommended_action,
        rejection_reason=gate_failure_reason,
    )


def build_rating_table_decision(
    *,
    lane_context: SurveyorLaneContext,
    thesis: MispricingThesis,
    evaluation: EvaluationReport,
    margin_of_safety: MarginOfSafetyAssessment,
    is_existing_position: bool,
    decision_date: str,
) -> RatingTableDecision:
    """Assemble the deterministic post-Appraiser decision row for persistence and JSON."""
    if thesis.ticker.casefold() != evaluation.ticker.casefold():
        msg = (
            f"Thesis ticker {thesis.ticker!r} does not match evaluation "
            f"{evaluation.ticker!r}."
        )
        raise ValueError(msg)
    if thesis.ticker.casefold() != lane_context.ticker.casefold():
        msg = (
            f"Thesis ticker {thesis.ticker!r} does not match lane context "
            f"{lane_context.ticker!r}."
        )
        raise ValueError(msg)

    sentinel_has_reservations = (
        evaluation.thesis_verdict == ThesisVerdict.INTACT_WITH_RESERVATIONS
    )
    rating, recommended_action = rating_from_table_inputs(
        margin_of_safety_verdict=margin_of_safety.margin_of_safety_verdict,
        conviction=thesis.conviction_level,
        sentinel_has_reservations=sentinel_has_reservations,
        is_existing_position=is_existing_position,
    )
    mos_label = margin_of_safety.margin_of_safety_verdict
    res_note = (
        "Sentinel returned reservations on the thesis."
        if sentinel_has_reservations
        else "Sentinel cleared the thesis without reservations."
    )
    primary = (
        f"Deterministic rating table ({mos_label}; Strategist conviction "
        f"{thesis.conviction_level}; {res_note})."
    )
    red_disp = (
        f"Red-flag screen: {evaluation.red_flag_screen.overall_red_flag_verdict.value}."
    )
    gap_disp = (
        "Material data gaps noted in Sentinel output; table path does not re-open them."
    )
    return RatingTableDecision(
        decision_rule_id="rating_table_v1",
        ticker=lane_context.ticker,
        company_name=lane_context.company_name,
        decision_date=decision_date,
        is_existing_position=is_existing_position,
        rating=rating,
        recommended_action=recommended_action,
        conviction=thesis.conviction_level,
        margin_of_safety=margin_of_safety,
        rationale=RatingTableRationale(
            primary_driver=primary,
            supporting_factors=[],
            mitigating_factors=[],
            red_flag_disposition=red_disp,
            data_gap_disposition=gap_disp,
        ),
        thesis_expiry_note=(
            f"Revisit thesis per Strategist resolution_mechanism: "
            f"{thesis.resolution_mechanism}"
        ),
    )


def verdict_from_decision(
    decision: RatingTableDecision | SentinelRejection | DataQualityRejection,
) -> Verdict:
    """Wrap a decision in ``Verdict`` with hoisted fields matching ``decision``."""
    return Verdict(
        ticker=decision.ticker,
        company_name=decision.company_name,
        decision_date=decision.decision_date,
        is_existing_position=decision.is_existing_position,
        rating=decision.rating,
        recommended_action=decision.recommended_action,
        decision=decision,
    )
