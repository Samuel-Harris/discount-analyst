"""Append-only USD costs for dashboard agent attempts."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from sqlmodel import Session, col, select

from discount_analyst.adapters.persistence.crud.db_utils import new_id, utc_now
from discount_analyst.adapters.persistence.models import (
    AgentAttemptCost,
    AgentExecution,
    AttemptOutcomeDb,
)
from discount_analyst.domain.workflow_cost import AttemptCost, RecordedAttempt


def insert_attempt_cost_once(
    session: Session,
    *,
    execution_id: str,
    successful: bool,
    attempt_cost: AttemptCost,
) -> None:
    """Store spend for the execution's current attempt. A second write is a no-op."""
    execution = session.get(AgentExecution, execution_id)
    if execution is None or execution.started_at is None:
        return
    started_at = _as_utc(execution.started_at)
    already_recorded = session.scalars(
        select(AgentAttemptCost).where(
            col(AgentAttemptCost.agent_execution_id) == execution_id
        )
    )
    if any(_as_utc(row.recorded_at) >= started_at for row in already_recorded):
        return
    session.add(
        AgentAttemptCost(
            id=new_id(),
            agent_execution_id=execution_id,
            outcome=(
                AttemptOutcomeDb.SUCCESSFUL
                if successful
                else AttemptOutcomeDb.UNSUCCESSFUL
            ),
            cost_usd=attempt_cost.cost_usd,
            recorded_at=utc_now(),
        )
    )


def list_recorded_attempts(
    session: Session, execution_ids: list[str]
) -> list[RecordedAttempt]:
    if not execution_ids:
        return []
    rows = session.exec(
        select(AgentAttemptCost, AgentExecution)
        .join(
            AgentExecution,
            col(AgentAttemptCost.agent_execution_id) == col(AgentExecution.id),
        )
        .where(
            col(AgentAttemptCost.agent_execution_id).in_(execution_ids)  # pyright: ignore[reportAttributeAccessIssue]
        )
    ).all()
    recorded: list[RecordedAttempt] = []
    for cost, execution in rows:
        recorded.append(
            RecordedAttempt(
                agent_execution_id=execution.id,
                agent_name=execution.agent_name.value,
                successful=cost.outcome == AttemptOutcomeDb.SUCCESSFUL,
                cost_usd=_decimal_or_none(cost.cost_usd),
            )
        )
    return recorded


def _decimal_or_none(value: Decimal | float | None) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
