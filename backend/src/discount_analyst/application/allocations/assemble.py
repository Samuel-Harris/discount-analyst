"""Build compact Allocator input from completed lane bundles and a snapshot."""

from dataclasses import dataclass
from datetime import date
from typing import Literal

from discount_analyst.agents.allocator.schema import (
    AllocatorInput,
    AllocatorLaneEvidence,
    CompactAppraiserEvidence,
    CompactResearcherEvidence,
    CompactSentinelEvidence,
    CompactStrategistEvidence,
    DataQualityRejectionLaneEvidence,
    RatingTableLaneEvidence,
    SentinelRejectionLaneEvidence,
    AllocatorLaneIdentity,
)
from discount_analyst.agents.appraiser.schema import AppraiserOutput
from discount_analyst.agents.researcher.schema import DeepResearchReport
from discount_analyst.agents.sentinel.schema import EvaluationReport, ThesisVerdict
from discount_analyst.agents.strategist.schema import MispricingThesis
from discount_analyst.application.allocations.errors import AllocationAssemblyError
from discount_analyst.domain.allocations.eligibility import allocation_policy_for
from discount_analyst.domain.allocations.snapshot import (
    CurrentPortfolioSnapshot,
    snapshot_weight_for_ticker,
)
from discount_analyst.domain.decisions.investment_rating import InvestmentRating
from discount_analyst.domain.decisions.margin_of_safety import MarginOfSafetyAssessment
from discount_analyst.domain.decisions.schema import Verdict

LaneDecisionKind = Literal[
    "rating_table", "sentinel_rejection", "data_quality_rejection"
]


@dataclass(frozen=True, slots=True)
class CompletedLaneBundle:
    source_run_id: str
    ticker: str
    company_name: str
    is_existing_position: bool
    rating: InvestmentRating
    decision_kind: LaneDecisionKind
    rejection_reason: str | None
    sector: str
    industry: str
    deep_research: DeepResearchReport | None = None
    thesis: MispricingThesis | None = None
    evaluation: EvaluationReport | None = None
    appraiser_output: AppraiserOutput | None = None


def completed_lane_bundle_from_verdict(
    *,
    source_run_id: str,
    verdict: Verdict,
    sector: str,
    industry: str,
    deep_research: DeepResearchReport | None = None,
    thesis: MispricingThesis | None = None,
    evaluation: EvaluationReport | None = None,
    appraiser_output: AppraiserOutput | None = None,
) -> CompletedLaneBundle:
    decision = verdict.decision
    rejection_reason = (
        None if decision.decision_kind == "rating_table" else decision.rejection_reason
    )
    return CompletedLaneBundle(
        source_run_id=source_run_id,
        ticker=verdict.ticker,
        company_name=verdict.company_name,
        is_existing_position=verdict.is_existing_position,
        rating=verdict.rating,
        decision_kind=decision.decision_kind,
        rejection_reason=rejection_reason,
        sector=sector,
        industry=industry,
        deep_research=deep_research,
        thesis=thesis,
        evaluation=evaluation,
        appraiser_output=appraiser_output,
    )


def source_run_ids_by_ticker(
    lane_bundles: tuple[CompletedLaneBundle, ...],
) -> dict[str, str]:
    indexed: dict[str, str] = {}
    for bundle in lane_bundles:
        key = bundle.ticker.casefold()
        if key in indexed:
            msg = f"Duplicate lane bundle ticker {bundle.ticker!r}."
            raise AllocationAssemblyError(msg)
        indexed[key] = bundle.source_run_id
    return indexed


def assemble_allocator_input(
    lanes: tuple[CompletedLaneBundle, ...],
    snapshot: CurrentPortfolioSnapshot,
    allocation_date: date,
) -> AllocatorInput:
    """Apply canonical policy and pack discriminated compact evidence."""
    _validate_snapshot_matches_lanes(lanes, snapshot)
    packed = tuple(_pack_lane(bundle, snapshot) for bundle in lanes)
    return AllocatorInput(
        allocation_date=allocation_date,
        snapshot=snapshot,
        lanes=packed,
    )


def _validate_snapshot_matches_lanes(
    lanes: tuple[CompletedLaneBundle, ...],
    snapshot: CurrentPortfolioSnapshot,
) -> None:
    lane_keys = {bundle.ticker.casefold(): bundle for bundle in lanes}
    snapshot_keys = {
        position.ticker.casefold(): position.ticker for position in snapshot.positions
    }
    for key, bundle in lane_keys.items():
        if key in snapshot_keys:
            continue
        if bundle.is_existing_position:
            msg = (
                "Existing-position lane "
                f"{bundle.ticker!r} is missing from the current "
                "portfolio snapshot."
            )
            raise AllocationAssemblyError(msg)
    for key, ticker in snapshot_keys.items():
        if key not in lane_keys:
            msg = f"Snapshot position {ticker!r} has no completed lane."
            raise AllocationAssemblyError(msg)


def _pack_lane(
    bundle: CompletedLaneBundle,
    snapshot: CurrentPortfolioSnapshot,
) -> AllocatorLaneEvidence:
    current_weight = snapshot_weight_for_ticker(snapshot, bundle.ticker)
    if current_weight is None:
        current_weight = 0.0
    policy = allocation_policy_for(
        rating=bundle.rating,
        is_existing_position=bundle.is_existing_position,
        current_weight_pct=current_weight,
    )
    identity = AllocatorLaneIdentity(
        ticker=bundle.ticker,
        company_name=bundle.company_name,
        is_existing_position=bundle.is_existing_position,
        current_weight_pct=current_weight,
        sector=bundle.sector,
        industry=bundle.industry,
        policy=policy,
        rating=bundle.rating,
    )
    if bundle.decision_kind == "rating_table":
        return RatingTableLaneEvidence(
            identity=identity,
            researcher=_require_researcher(bundle),
            strategist=_require_strategist(bundle),
            sentinel=_require_sentinel(bundle),
            appraiser=_require_appraiser(bundle),
        )
    if bundle.decision_kind == "sentinel_rejection":
        if bundle.appraiser_output is not None:
            msg = (
                f"Sentinel-rejection lane {bundle.ticker!r} cannot "
                "carry Appraiser valuation evidence."
            )
            raise AllocationAssemblyError(msg)
        return SentinelRejectionLaneEvidence(
            identity=identity,
            rejection_reason=_require_rejection_reason(bundle),
            researcher=_require_researcher(bundle),
            strategist=_require_strategist(bundle),
            sentinel=_require_sentinel(bundle),
        )
    if (
        bundle.deep_research is not None
        or bundle.thesis is not None
        or bundle.evaluation is not None
        or bundle.appraiser_output is not None
    ):
        msg = (
            f"Data-quality rejection lane {bundle.ticker!r} cannot "
            "carry research, thesis, Sentinel, or valuation evidence."
        )
        raise AllocationAssemblyError(msg)
    return DataQualityRejectionLaneEvidence(
        identity=identity,
        rejection_reason=_require_rejection_reason(bundle),
    )


def _require_rejection_reason(bundle: CompletedLaneBundle) -> str:
    if bundle.rejection_reason is None:
        msg = f"Lane {bundle.ticker!r} is missing a rejection reason."
        raise AllocationAssemblyError(msg)
    return bundle.rejection_reason


def _require_researcher(bundle: CompletedLaneBundle) -> CompactResearcherEvidence:
    report = bundle.deep_research
    if report is None:
        msg = f"Lane {bundle.ticker!r} is missing Researcher evidence."
        raise AllocationAssemblyError(msg)
    return CompactResearcherEvidence(
        customer_segments=report.business_model.customer_segments,
        risks=tuple(report.risks),
    )


def _require_strategist(bundle: CompletedLaneBundle) -> CompactStrategistEvidence:
    thesis = bundle.thesis
    if thesis is None:
        msg = f"Lane {bundle.ticker!r} is missing Strategist evidence."
        raise AllocationAssemblyError(msg)
    return CompactStrategistEvidence(
        thesis_summary=thesis.mispricing_argument,
        conviction=thesis.conviction_level,
        thesis_risks=tuple(thesis.thesis_risks),
        permanent_loss_scenarios=tuple(thesis.permanent_loss_scenarios),
    )


def _require_sentinel(bundle: CompletedLaneBundle) -> CompactSentinelEvidence:
    evaluation = bundle.evaluation
    if evaluation is None:
        msg = f"Lane {bundle.ticker!r} is missing Sentinel evidence."
        raise AllocationAssemblyError(msg)
    return CompactSentinelEvidence(
        customer_or_supplier_concentration=(
            evaluation.red_flag_screen.customer_or_supplier_concentration
        ),
        red_flag_verdict=evaluation.red_flag_screen.overall_red_flag_verdict.value,
        reservations=(
            evaluation.thesis_verdict is ThesisVerdict.INTACT_WITH_RESERVATIONS
        ),
        material_data_gaps=evaluation.material_data_gaps,
    )


def _require_appraiser(bundle: CompletedLaneBundle) -> CompactAppraiserEvidence:
    output = bundle.appraiser_output
    if output is None:
        msg = f"Lane {bundle.ticker!r} is missing Appraiser evidence."
        raise AllocationAssemblyError(msg)
    margin = MarginOfSafetyAssessment.from_distribution(output.valuation_distribution)
    return CompactAppraiserEvidence(
        current_price=margin.current_price,
        expected_value=margin.expected_intrinsic_value,
        p10=margin.p10_intrinsic_value,
        p90=margin.p90_intrinsic_value,
        margin_of_safety_base_pct=margin.margin_of_safety_base_pct,
        data_quality=output.data_quality,
    )
