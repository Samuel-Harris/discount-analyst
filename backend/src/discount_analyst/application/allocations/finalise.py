"""Stamp audit facts onto a Curator proposal without changing its numbers."""

from pydantic import ValidationError

from discount_analyst.agents.curator.schema import (
    AppraisedLaneEvidence,
    CuratorInput,
    CuratorProposal,
    ProposedCash,
    ProposedPosition,
)
from discount_analyst.application.allocations.assemble import (
    AssembledCuratorJob,
    DqrStampLane,
)
from discount_analyst.application.allocations.errors import AllocationAssemblyError
from discount_analyst.domain.allocations.actions import derive_rebalance_action
from discount_analyst.domain.allocations.allocation import (
    AllocationPosition,
    CashAllocation,
    PortfolioAllocation,
    SharedRiskCluster,
)
from discount_analyst.domain.allocations.invariants import AllocationInvariantError


def finalise_curator_proposal(
    proposal: CuratorProposal,
    job: AssembledCuratorJob,
) -> PortfolioAllocation:
    """Stamp identity facts; ``PortfolioAllocation`` is the numeric gate."""
    curator_input = job.curator_input
    if proposal.allocation_date != curator_input.allocation_date:
        msg = (
            "Proposal allocation_date "
            f"{proposal.allocation_date.isoformat()} does not match input "
            f"{curator_input.allocation_date.isoformat()}."
        )
        raise AllocationInvariantError(msg)
    lanes_by_ticker = {
        lane.identity.ticker.casefold(): lane for lane in curator_input.lanes
    }
    _assert_identical_ticker_sets(proposal, curator_input)
    valued_positions = tuple(
        _stamp_valued_position(
            proposed,
            lanes_by_ticker[proposed.ticker.casefold()],
            job.source_run_ids,
        )
        for proposed in proposal.positions
    )
    dqr_positions = tuple(_stamp_dqr_zero(stamp) for stamp in job.dqr_stamps)
    try:
        return PortfolioAllocation(
            allocation_date=proposal.allocation_date,
            positions=(*valued_positions, *dqr_positions),
            cash=CashAllocation(
                current_weight_pct=job.ledger_cash_weight_pct,
                target_weight_pct=proposal.cash.target_weight_pct,
                acceptable_weight_low_pct=proposal.cash.acceptable_weight_low_pct,
                acceptable_weight_high_pct=proposal.cash.acceptable_weight_high_pct,
                rationale=proposal.cash.rationale,
            ),
            shared_risk_clusters=tuple(
                SharedRiskCluster(
                    label=cluster.label,
                    member_tickers=cluster.member_tickers,
                    mechanism=cluster.mechanism,
                    allocation_effect=cluster.allocation_effect,
                )
                for cluster in proposal.shared_risk_clusters
            ),
            portfolio_rationale=proposal.portfolio_rationale,
        )
    except ValidationError as exc:
        raise AllocationInvariantError(str(exc)) from exc


def synthesise_cash_only_allocation(job: AssembledCuratorJob) -> PortfolioAllocation:
    """Cash-only book when every lane is DQR (or there are no valued lanes)."""
    cash_proposal = ProposedCash(
        target_weight_pct=100.0,
        acceptable_weight_low_pct=100.0,
        acceptable_weight_high_pct=100.0,
        rationale="No valued names; residual capital held in cash.",
    )
    empty_proposal = CuratorProposal(
        allocation_date=job.curator_input.allocation_date,
        positions=(),
        cash=cash_proposal,
        shared_risk_clusters=(),
        portfolio_rationale=(
            "Every ticker failed the data-quality gate; the book is cash plus "
            "stamped zeros."
            if job.dqr_stamps
            else "No valued names; the book is cash."
        ),
    )
    return finalise_curator_proposal(empty_proposal, job)


def _assert_identical_ticker_sets(
    proposal: CuratorProposal,
    curator_input: CuratorInput,
) -> None:
    proposed = {position.ticker.casefold() for position in proposal.positions}
    expected = {lane.identity.ticker.casefold() for lane in curator_input.lanes}
    if proposed != expected:
        msg = (
            "Proposal tickers must equal input tickers exactly; "
            f"missing={sorted(expected - proposed)}, "
            f"unexpected={sorted(proposed - expected)}."
        )
        raise AllocationInvariantError(msg)


def _stamp_valued_position(
    proposed: ProposedPosition,
    lane: AppraisedLaneEvidence,
    source_run_ids: dict[str, str],
) -> AllocationPosition:
    identity = lane.identity
    if proposed.ticker.casefold() != identity.ticker.casefold():
        msg = (
            f"Proposal ticker {proposed.ticker!r} does not match lane "
            f"{identity.ticker!r}."
        )
        raise AllocationInvariantError(msg)
    source_run_id = source_run_ids.get(proposed.ticker.casefold())
    if source_run_id is None:
        msg = f"Proposal ticker {proposed.ticker!r} has no source_run_id."
        raise AllocationAssemblyError(msg)
    action = derive_rebalance_action(
        current_weight_pct=identity.current_weight_pct,
        target_weight_pct=proposed.target_weight_pct,
        acceptable_weight_low_pct=proposed.acceptable_weight_low_pct,
        acceptable_weight_high_pct=proposed.acceptable_weight_high_pct,
        is_existing_position=identity.is_existing_position,
    )
    return AllocationPosition(
        ticker=proposed.ticker,
        company_name=identity.company_name,
        source_run_id=source_run_id,
        is_existing_position=identity.is_existing_position,
        current_weight_pct=identity.current_weight_pct,
        target_weight_pct=proposed.target_weight_pct,
        acceptable_weight_low_pct=proposed.acceptable_weight_low_pct,
        acceptable_weight_high_pct=proposed.acceptable_weight_high_pct,
        action=action,
        rationale=proposed.rationale,
    )


def _stamp_dqr_zero(stamp: DqrStampLane) -> AllocationPosition:
    action = derive_rebalance_action(
        current_weight_pct=stamp.current_weight_pct,
        target_weight_pct=0.0,
        acceptable_weight_low_pct=0.0,
        acceptable_weight_high_pct=0.0,
        is_existing_position=stamp.is_existing_position,
    )
    return AllocationPosition(
        ticker=stamp.ticker,
        company_name=stamp.company_name,
        source_run_id=stamp.source_run_id,
        is_existing_position=stamp.is_existing_position,
        current_weight_pct=stamp.current_weight_pct,
        target_weight_pct=0.0,
        acceptable_weight_low_pct=0.0,
        acceptable_weight_high_pct=0.0,
        action=action,
        rationale=stamp.rationale,
    )
