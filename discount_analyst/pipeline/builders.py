from __future__ import annotations

from discount_analyst.agents.arbiter.schema import ArbiterDecision
from discount_analyst.agents.sentinel.schema import (
    EvaluationReport,
    OverallRedFlagVerdict,
    ThesisVerdict,
)
from discount_analyst.agents.strategist.schema import MispricingThesis
from discount_analyst.pipeline.schema import SentinelRejection, Verdict
from discount_analyst.rating import InvestmentRating


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


def verdict_from_decision(decision: ArbiterDecision | SentinelRejection) -> Verdict:
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
