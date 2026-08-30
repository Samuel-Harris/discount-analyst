"""Persist and reconstruct workflow-level ``PortfolioAllocation`` rows."""

from __future__ import annotations

from sqlmodel import Session, col, delete, select

from discount_analyst.adapters.persistence.crud.db_utils import new_id
from discount_analyst.adapters.persistence.models import (
    AgentExecution,
    AgentNameDb,
    AllocationPolicyKindDb,
    ExecutionStatusDb,
    ForcedZeroReasonDb,
    PortfolioAllocation,
    PortfolioAllocationPosition,
    PortfolioAllocationRiskCluster,
    PortfolioAllocationRiskClusterMember,
    RebalanceActionDb,
)
from discount_analyst.domain.allocations.actions import RebalanceAction
from discount_analyst.domain.allocations.allocation import (
    AllocationPosition,
    CashAllocation,
    PortfolioAllocation as DomainPortfolioAllocation,
    SharedRiskCluster,
)
from discount_analyst.domain.allocations.policy import (
    ForcedZeroPolicy,
    ForcedZeroReason,
    InvestablePolicy,
    RetainOrReducePolicy,
)


def persist_portfolio_allocation(
    session: Session,
    *,
    agent_execution_id: str,
    allocation: DomainPortfolioAllocation,
) -> None:
    """Store a fully validated allocation. Replaces any previous rows for the execution."""
    delete_portfolio_allocation_for_execution(session, agent_execution_id)
    header = PortfolioAllocation(
        id=new_id(),
        agent_execution_id=agent_execution_id,
        allocation_date=allocation.allocation_date,
        current_cash_weight_pct=allocation.cash.current_weight_pct,
        cash_target_weight_pct=allocation.cash.target_weight_pct,
        cash_acceptable_weight_low_pct=allocation.cash.acceptable_weight_low_pct,
        cash_acceptable_weight_high_pct=allocation.cash.acceptable_weight_high_pct,
        cash_rationale=allocation.cash.rationale,
        portfolio_rationale=allocation.portfolio_rationale,
    )
    session.add(header)
    positions_by_ticker: dict[str, PortfolioAllocationPosition] = {}
    for sort_order, position in enumerate(allocation.positions):
        policy_kind, forced_zero_reason = _policy_columns(position)
        row = PortfolioAllocationPosition(
            id=new_id(),
            allocation_id=header.id,
            source_run_id=position.source_run_id,
            sort_order=sort_order,
            ticker=position.ticker,
            company_name=position.company_name,
            is_existing_position=position.is_existing_position,
            current_weight_pct=position.current_weight_pct,
            policy_kind=policy_kind,
            forced_zero_reason=forced_zero_reason,
            target_weight_pct=position.target_weight_pct,
            acceptable_weight_low_pct=position.acceptable_weight_low_pct,
            acceptable_weight_high_pct=position.acceptable_weight_high_pct,
            action=RebalanceActionDb(position.action.value),
            rationale=position.rationale,
        )
        session.add(row)
        positions_by_ticker[position.ticker.casefold()] = row
    for cluster_order, cluster in enumerate(allocation.shared_risk_clusters):
        cluster_row = PortfolioAllocationRiskCluster(
            id=new_id(),
            allocation_id=header.id,
            sort_order=cluster_order,
            label=cluster.label,
            mechanism=cluster.mechanism,
            allocation_effect=cluster.allocation_effect,
        )
        session.add(cluster_row)
        for member_order, ticker in enumerate(cluster.member_tickers):
            member_position = positions_by_ticker[ticker.casefold()]
            session.add(
                PortfolioAllocationRiskClusterMember(
                    id=new_id(),
                    cluster_id=cluster_row.id,
                    allocation_position_id=member_position.id,
                    sort_order=member_order,
                )
            )


def delete_portfolio_allocation_for_execution(
    session: Session, agent_execution_id: str
) -> None:
    header = session.scalars(
        select(PortfolioAllocation).where(
            col(PortfolioAllocation.agent_execution_id) == agent_execution_id
        )
    ).first()
    if header is None:
        return
    cluster_ids = list(
        session.scalars(
            select(col(PortfolioAllocationRiskCluster.id)).where(
                col(PortfolioAllocationRiskCluster.allocation_id) == header.id
            )
        )
    )
    if cluster_ids:
        session.exec(
            delete(PortfolioAllocationRiskClusterMember).where(
                col(PortfolioAllocationRiskClusterMember.cluster_id).in_(cluster_ids)
            )
        )
    session.exec(
        delete(PortfolioAllocationRiskCluster).where(
            col(PortfolioAllocationRiskCluster.allocation_id) == header.id
        )
    )
    session.exec(
        delete(PortfolioAllocationPosition).where(
            col(PortfolioAllocationPosition.allocation_id) == header.id
        )
    )
    session.exec(
        delete(PortfolioAllocation).where(col(PortfolioAllocation.id) == header.id)
    )


def get_portfolio_allocation_for_execution(
    session: Session, agent_execution_id: str
) -> DomainPortfolioAllocation | None:
    header = session.scalars(
        select(PortfolioAllocation).where(
            col(PortfolioAllocation.agent_execution_id) == agent_execution_id
        )
    ).first()
    if header is None:
        return None
    return _reconstruct(session, header)


def get_portfolio_allocation_for_workflow(
    session: Session, workflow_run_id: str
) -> DomainPortfolioAllocation | None:
    execution = session.scalars(
        select(AgentExecution).where(
            col(AgentExecution.workflow_run_id) == workflow_run_id,
            col(AgentExecution.agent_name) == AgentNameDb.ALLOCATOR,
        )
    ).first()
    if execution is None or execution.status != ExecutionStatusDb.COMPLETED:
        return None
    return get_portfolio_allocation_for_execution(session, execution.id)


def _policy_columns(
    position: AllocationPosition,
) -> tuple[AllocationPolicyKindDb, ForcedZeroReasonDb | None]:
    if position.policy.kind == "investable":
        return AllocationPolicyKindDb.INVESTABLE, None
    if position.policy.kind == "retain_or_reduce":
        return AllocationPolicyKindDb.RETAIN_OR_REDUCE, None
    return (
        AllocationPolicyKindDb.FORCED_ZERO,
        ForcedZeroReasonDb(position.policy.reason.value),
    )


def _reconstruct(
    session: Session, header: PortfolioAllocation
) -> DomainPortfolioAllocation:
    position_rows = list(
        session.scalars(
            select(PortfolioAllocationPosition)
            .where(col(PortfolioAllocationPosition.allocation_id) == header.id)
            .order_by(col(PortfolioAllocationPosition.sort_order))
        )
    )
    positions_by_id = {row.id: row for row in position_rows}
    cluster_rows = list(
        session.scalars(
            select(PortfolioAllocationRiskCluster)
            .where(col(PortfolioAllocationRiskCluster.allocation_id) == header.id)
            .order_by(col(PortfolioAllocationRiskCluster.sort_order))
        )
    )
    clusters: list[SharedRiskCluster] = []
    for cluster_row in cluster_rows:
        members = list(
            session.scalars(
                select(PortfolioAllocationRiskClusterMember)
                .where(
                    col(PortfolioAllocationRiskClusterMember.cluster_id)
                    == cluster_row.id
                )
                .order_by(col(PortfolioAllocationRiskClusterMember.sort_order))
            )
        )
        tickers = tuple(
            positions_by_id[member.allocation_position_id].ticker for member in members
        )
        clusters.append(
            SharedRiskCluster(
                label=cluster_row.label,
                member_tickers=tickers,
                mechanism=cluster_row.mechanism,
                allocation_effect=cluster_row.allocation_effect,
            )
        )
    return DomainPortfolioAllocation(
        allocation_date=header.allocation_date,
        positions=tuple(_position_from_row(row) for row in position_rows),
        cash=CashAllocation(
            current_weight_pct=header.current_cash_weight_pct,
            target_weight_pct=header.cash_target_weight_pct,
            acceptable_weight_low_pct=header.cash_acceptable_weight_low_pct,
            acceptable_weight_high_pct=header.cash_acceptable_weight_high_pct,
            rationale=header.cash_rationale,
        ),
        shared_risk_clusters=tuple(clusters),
        portfolio_rationale=header.portfolio_rationale,
    )


def _position_from_row(row: PortfolioAllocationPosition) -> AllocationPosition:
    if row.policy_kind == AllocationPolicyKindDb.INVESTABLE:
        policy = InvestablePolicy()
    elif row.policy_kind == AllocationPolicyKindDb.RETAIN_OR_REDUCE:
        policy = RetainOrReducePolicy(current_weight_pct=row.current_weight_pct)
    else:
        if row.forced_zero_reason is None:
            msg = f"Forced-zero position {row.ticker!r} is missing a reason."
            raise ValueError(msg)
        policy = ForcedZeroPolicy(reason=ForcedZeroReason(row.forced_zero_reason.value))
    return AllocationPosition(
        ticker=row.ticker,
        company_name=row.company_name,
        source_run_id=row.source_run_id,
        is_existing_position=row.is_existing_position,
        current_weight_pct=row.current_weight_pct,
        policy=policy,
        target_weight_pct=row.target_weight_pct,
        acceptable_weight_low_pct=row.acceptable_weight_low_pct,
        acceptable_weight_high_pct=row.acceptable_weight_high_pct,
        action=RebalanceAction(row.action.value),
        rationale=row.rationale,
    )
