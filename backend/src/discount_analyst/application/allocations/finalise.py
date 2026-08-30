"""Stamp audit facts onto an Allocator proposal without changing its numbers."""

from pydantic import ValidationError

from discount_analyst.agents.allocator.schema import (
    AllocatorInput,
    AllocatorLaneEvidence,
    AllocatorProposal,
    ProposedPosition,
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


def finalise_allocator_proposal(
    proposal: AllocatorProposal,
    allocator_input: AllocatorInput,
    source_run_ids: dict[str, str],
) -> PortfolioAllocation:
    """Stamp identity facts; ``PortfolioAllocation`` is the numeric gate."""
    if proposal.allocation_date != allocator_input.allocation_date:
        msg = (
            "Proposal allocation_date "
            f"{proposal.allocation_date.isoformat()} does not match input "
            f"{allocator_input.allocation_date.isoformat()}."
        )
        raise AllocationInvariantError(msg)
    lanes_by_ticker = {
        lane.identity.ticker.casefold(): lane for lane in allocator_input.lanes
    }
    _assert_identical_ticker_sets(proposal, allocator_input)
    positions = tuple(
        _stamp_position(
            proposed,
            lanes_by_ticker[proposed.ticker.casefold()],
            source_run_ids,
        )
        for proposed in proposal.positions
    )
    try:
        return PortfolioAllocation(
            allocation_date=proposal.allocation_date,
            positions=positions,
            cash=CashAllocation(
                current_weight_pct=allocator_input.snapshot.cash_weight_pct,
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


def _assert_identical_ticker_sets(
    proposal: AllocatorProposal,
    allocator_input: AllocatorInput,
) -> None:
    proposed = {position.ticker.casefold() for position in proposal.positions}
    expected = {lane.identity.ticker.casefold() for lane in allocator_input.lanes}
    if proposed != expected:
        msg = (
            "Proposal tickers must equal input tickers exactly; "
            f"missing={sorted(expected - proposed)}, "
            f"unexpected={sorted(proposed - expected)}."
        )
        raise AllocationInvariantError(msg)


def _stamp_position(
    proposed: ProposedPosition,
    lane: AllocatorLaneEvidence,
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
        policy=identity.policy,
        target_weight_pct=proposed.target_weight_pct,
        acceptable_weight_low_pct=proposed.acceptable_weight_low_pct,
        acceptable_weight_high_pct=proposed.acceptable_weight_high_pct,
        action=action,
        rationale=proposed.rationale,
    )
