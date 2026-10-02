from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from sqlmodel import Session, col, select

from backend.tests.factories.sterling import sterling_holdings
from discount_analyst.adapters.persistence.crud.attempt_costs import (
    insert_attempt_cost_once,
)
from discount_analyst.adapters.persistence.crud.db_utils import new_id
from discount_analyst.adapters.persistence.crud.run_executions import (
    update_agent_execution,
)
from discount_analyst.adapters.persistence.crud.workflow_runs import (
    fetch_workflow_detail,
    insert_workflow_run,
)
from discount_analyst.adapters.persistence.models import AgentAttemptCost
from discount_analyst.domain.workflow_cost import AttemptCost


def test_insert_attempt_cost_once_keeps_each_attempt(
    db_session: Session,
) -> None:
    workflow_run_id = new_id()
    surveyor_execution_id = new_id()
    insert_workflow_run(
        db_session,
        workflow_run_id=workflow_run_id,
        holdings=sterling_holdings("ABC.L"),
        suggestion_tickers=(),
        cash_gbp=Decimal("0"),
        is_mock=False,
        surveyor_execution_id=surveyor_execution_id,
    )
    update_agent_execution(
        db_session,
        execution_id=surveyor_execution_id,
        status="running",
        started_at="2020-01-01T00:00:00Z",
    )
    priced = AttemptCost(cost_usd=Decimal("1.25"))
    insert_attempt_cost_once(
        db_session,
        execution_id=surveyor_execution_id,
        successful=False,
        attempt_cost=priced,
    )
    insert_attempt_cost_once(
        db_session,
        execution_id=surveyor_execution_id,
        successful=False,
        attempt_cost=priced,
    )
    db_session.commit()

    first_rows = list(db_session.scalars(select(AgentAttemptCost)))
    assert len(first_rows) == 1
    first_rows[0].recorded_at = datetime(2020, 1, 1, tzinfo=UTC)
    db_session.add(first_rows[0])
    update_agent_execution(
        db_session,
        execution_id=surveyor_execution_id,
        status="running",
        started_at="2026-06-01T00:00:00Z",
    )
    insert_attempt_cost_once(
        db_session,
        execution_id=surveyor_execution_id,
        successful=True,
        attempt_cost=AttemptCost(cost_usd=Decimal("2.50")),
    )
    db_session.commit()

    detail = fetch_workflow_detail(db_session, workflow_run_id)
    assert detail is not None
    assert detail["cost_total"] == {"state": "amount", "amount_usd": "3.75"}
    assert detail["cost_unsuccessful"] == {"state": "amount", "amount_usd": "1.25"}
    assert detail["cost_successful"] == {"state": "amount", "amount_usd": "2.50"}
    surveyor = detail["surveyor_execution"]
    assert surveyor is not None
    assert surveyor["cost"] == {"state": "amount", "amount_usd": "3.75"}
    assert len(list(db_session.scalars(select(AgentAttemptCost)))) == 2
    assert db_session.scalars(
        select(AgentAttemptCost).where(
            col(AgentAttemptCost.agent_execution_id) == surveyor_execution_id
        )
    ).all()
