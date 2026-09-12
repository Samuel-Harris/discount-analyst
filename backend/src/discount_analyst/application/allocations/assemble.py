"""Build compact Curator input from completed lane bundles and a snapshot."""

from dataclasses import dataclass
from datetime import date

from discount_analyst.agents.appraiser.schema import AppraiserOutput
from discount_analyst.agents.curator.schema import (
    AppraisedLaneEvidence,
    CompactAppraiserEvidence,
    CompactResearcherEvidence,
    CompactSentinelEvidence,
    CompactStrategistEvidence,
    CuratorInput,
    CuratorLaneIdentity,
    PackedMispricingThesis,
)
from discount_analyst.agents.researcher.schema import DeepResearchReport
from discount_analyst.agents.sentinel.schema import EvaluationReport
from discount_analyst.agents.strategist.schema import MispricingThesis
from discount_analyst.application.allocations.errors import AllocationAssemblyError
from discount_analyst.domain.allocations.snapshot import (
    CurrentPortfolioSnapshot,
    CurrentPositionWeight,
    snapshot_weight_for_ticker,
)
from discount_analyst.domain.decisions.margin_of_safety import MarginOfSafetyAssessment
from discount_analyst.domain.decisions.schema import (
    AppraisedDecision,
    DataQualityRejection,
)


@dataclass(frozen=True, slots=True)
class ValuedLaneBundle:
    source_run_id: str
    ticker: str
    company_name: str
    is_existing_position: bool
    sector: str
    industry: str
    deep_research: DeepResearchReport
    thesis: MispricingThesis
    evaluation: EvaluationReport
    appraiser_output: AppraiserOutput


@dataclass(frozen=True, slots=True)
class DqrLaneBundle:
    source_run_id: str
    ticker: str
    company_name: str
    is_existing_position: bool
    sector: str
    industry: str
    rationale: str


@dataclass(frozen=True, slots=True)
class DqrStampLane:
    source_run_id: str
    ticker: str
    company_name: str
    is_existing_position: bool
    current_weight_pct: float
    rationale: str


@dataclass(frozen=True, slots=True)
class AssembledCuratorJob:
    curator_input: CuratorInput
    dqr_stamps: tuple[DqrStampLane, ...]
    source_run_ids: dict[str, str]
    ledger_cash_weight_pct: float


def valued_lane_bundle(
    *,
    source_run_id: str,
    decision: AppraisedDecision,
    sector: str,
    industry: str,
    deep_research: DeepResearchReport,
    thesis: MispricingThesis,
    evaluation: EvaluationReport,
    appraiser_output: AppraiserOutput,
) -> ValuedLaneBundle:
    return ValuedLaneBundle(
        source_run_id=source_run_id,
        ticker=decision.ticker,
        company_name=decision.company_name,
        is_existing_position=decision.is_existing_position,
        sector=sector,
        industry=industry,
        deep_research=deep_research,
        thesis=thesis,
        evaluation=evaluation,
        appraiser_output=appraiser_output,
    )


def dqr_lane_bundle(
    *,
    source_run_id: str,
    decision: DataQualityRejection,
    sector: str,
    industry: str,
) -> DqrLaneBundle:
    return DqrLaneBundle(
        source_run_id=source_run_id,
        ticker=decision.ticker,
        company_name=decision.company_name,
        is_existing_position=decision.is_existing_position,
        sector=sector,
        industry=industry,
        rationale=f"Data-quality gate failed: {decision.rejection_reason}",
    )


def source_run_ids_by_ticker(
    valued: tuple[ValuedLaneBundle, ...],
    dqr: tuple[DqrLaneBundle, ...] = (),
) -> dict[str, str]:
    indexed: dict[str, str] = {}
    for bundle in (*valued, *dqr):
        key = bundle.ticker.casefold()
        if key in indexed:
            msg = f"Duplicate lane bundle ticker {bundle.ticker!r}."
            raise AllocationAssemblyError(msg)
        indexed[key] = bundle.source_run_id
    return indexed


def assemble_curator_job(
    valued: tuple[ValuedLaneBundle, ...],
    snapshot: CurrentPortfolioSnapshot,
    allocation_date: date,
    *,
    dqr: tuple[DqrLaneBundle, ...] = (),
) -> AssembledCuratorJob:
    """Pack valued lanes for the LLM; hold DQR names for application stamps."""
    _validate_snapshot_matches_lanes(valued, dqr, snapshot)
    packed = tuple(_pack_valued_lane(bundle, snapshot) for bundle in valued)
    stamps = tuple(_dqr_stamp(bundle, snapshot) for bundle in dqr)
    return AssembledCuratorJob(
        curator_input=CuratorInput(
            allocation_date=allocation_date,
            snapshot=_llm_snapshot(snapshot, dqr),
            lanes=packed,
        ),
        dqr_stamps=stamps,
        source_run_ids=source_run_ids_by_ticker(valued, dqr),
        ledger_cash_weight_pct=snapshot.cash_weight_pct,
    )


def _validate_snapshot_matches_lanes(
    valued: tuple[ValuedLaneBundle, ...],
    dqr: tuple[DqrLaneBundle, ...],
    snapshot: CurrentPortfolioSnapshot,
) -> None:
    lane_keys = {bundle.ticker.casefold(): bundle for bundle in (*valued, *dqr)}
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


def _llm_snapshot(
    snapshot: CurrentPortfolioSnapshot,
    dqr: tuple[DqrLaneBundle, ...],
) -> CurrentPortfolioSnapshot:
    """Hide unvalued holdings from the LLM; fold their current weight into cash."""
    dqr_keys = {bundle.ticker.casefold() for bundle in dqr}
    if not dqr_keys:
        return snapshot
    kept: list[CurrentPositionWeight] = []
    folded = 0.0
    for position in snapshot.positions:
        if position.ticker.casefold() in dqr_keys:
            folded += position.current_weight_pct
            continue
        kept.append(position)
    if folded == 0.0:
        return snapshot
    return CurrentPortfolioSnapshot(
        as_of=snapshot.as_of,
        positions=tuple(kept),
        cash_weight_pct=round(snapshot.cash_weight_pct + folded, 2),
    )


def _current_weight(ticker: str, snapshot: CurrentPortfolioSnapshot) -> float:
    current_weight = snapshot_weight_for_ticker(snapshot, ticker)
    if current_weight is None:
        return 0.0
    return current_weight


def _identity(
    bundle: ValuedLaneBundle,
    snapshot: CurrentPortfolioSnapshot,
) -> CuratorLaneIdentity:
    return CuratorLaneIdentity(
        ticker=bundle.ticker,
        company_name=bundle.company_name,
        is_existing_position=bundle.is_existing_position,
        current_weight_pct=_current_weight(bundle.ticker, snapshot),
        sector=bundle.sector,
        industry=bundle.industry,
    )


def _pack_valued_lane(
    bundle: ValuedLaneBundle,
    snapshot: CurrentPortfolioSnapshot,
) -> AppraisedLaneEvidence:
    return AppraisedLaneEvidence(
        identity=_identity(bundle, snapshot),
        live_thesis=_pack_live_thesis(bundle.thesis),
        researcher=CompactResearcherEvidence(
            customer_segments=bundle.deep_research.business_model.customer_segments,
            risks=tuple(bundle.deep_research.risks),
        ),
        strategist=_compact_strategist(bundle.thesis),
        sentinel=CompactSentinelEvidence(
            customer_or_supplier_concentration=(
                bundle.evaluation.red_flag_screen.customer_or_supplier_concentration
            ),
            red_flag_verdict=bundle.evaluation.red_flag_screen.overall_red_flag_verdict.value,
            thesis_verdict=bundle.evaluation.thesis_verdict.value,
            material_data_gaps=bundle.evaluation.material_data_gaps,
        ),
        appraiser=_compact_appraiser(bundle.appraiser_output),
    )


def _dqr_stamp(
    bundle: DqrLaneBundle, snapshot: CurrentPortfolioSnapshot
) -> DqrStampLane:
    return DqrStampLane(
        source_run_id=bundle.source_run_id,
        ticker=bundle.ticker,
        company_name=bundle.company_name,
        is_existing_position=bundle.is_existing_position,
        current_weight_pct=_current_weight(bundle.ticker, snapshot),
        rationale=bundle.rationale,
    )


def _pack_live_thesis(thesis: MispricingThesis) -> PackedMispricingThesis:
    return PackedMispricingThesis.model_validate(thesis.model_dump())


def _compact_strategist(thesis: MispricingThesis) -> CompactStrategistEvidence:
    return CompactStrategistEvidence(
        thesis_summary=thesis.mispricing_argument,
        conviction=thesis.conviction_level,
        thesis_risks=tuple(thesis.thesis_risks),
        permanent_loss_scenarios=tuple(thesis.permanent_loss_scenarios),
    )


def _compact_appraiser(output: AppraiserOutput) -> CompactAppraiserEvidence:
    margin = MarginOfSafetyAssessment.from_distribution(output.valuation_distribution)
    return CompactAppraiserEvidence(
        current_price=margin.current_price,
        expected_value=margin.expected_intrinsic_value,
        p10=margin.p10_intrinsic_value,
        p90=margin.p90_intrinsic_value,
        margin_of_safety_base_pct=margin.margin_of_safety_base_pct,
        data_quality=output.data_quality,
    )
