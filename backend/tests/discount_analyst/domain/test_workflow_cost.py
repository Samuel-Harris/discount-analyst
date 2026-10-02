from decimal import Decimal

import pytest

from discount_analyst.domain.workflow_cost import (
    RecordedAttempt,
    summarise_workflow_cost,
)


def _attempt(
    *,
    execution_id: str = "exec-1",
    agent_name: str = "researcher",
    successful: bool = True,
    cost_usd: Decimal | None = Decimal("1.00"),
) -> RecordedAttempt:
    return RecordedAttempt(
        agent_execution_id=execution_id,
        agent_name=agent_name,
        successful=successful,
        cost_usd=cost_usd,
    )


def test_empty_real_run_is_zero() -> None:
    summary = summarise_workflow_cost([], is_mock=False, execution_ids=["exec-1"])

    assert summary.total.amount_text() == "0.00"
    assert summary.successful.amount_text() == "0.00"
    assert summary.unsuccessful.amount_text() == "0.00"
    assert summary.figure_for_execution("exec-1").amount_text() == "0.00"
    assert summary.by_agent[0].agent_name == "surveyor"
    assert summary.by_agent[0].cost.amount_text() == "0.00"


def test_sums_priced_attempts_and_keeps_retry_spend() -> None:
    summary = summarise_workflow_cost(
        [
            _attempt(successful=False, cost_usd=Decimal("1.50")),
            _attempt(successful=True, cost_usd=Decimal("2.255")),
            _attempt(
                execution_id="exec-2",
                agent_name="appraiser",
                successful=True,
                cost_usd=Decimal("0.004"),
            ),
        ],
        is_mock=False,
        execution_ids=["exec-1", "exec-2"],
    )

    assert summary.total.amount_text() == "3.76"
    assert summary.successful.amount_text() == "2.26"
    assert summary.unsuccessful.amount_text() == "1.50"
    assert summary.figure_for_execution("exec-1").amount_text() == "3.76"
    researcher = next(
        agent for agent in summary.by_agent if agent.agent_name == "researcher"
    )
    appraiser = next(
        agent for agent in summary.by_agent if agent.agent_name == "appraiser"
    )
    assert researcher.cost.amount_text() == "3.76"
    assert appraiser.cost.amount_text() == "0.00"


def test_unpriced_attempts_are_omitted_until_nothing_is_priced() -> None:
    mixed = summarise_workflow_cost(
        [
            _attempt(cost_usd=Decimal("1.00")),
            _attempt(cost_usd=None, successful=False),
        ],
        is_mock=False,
        execution_ids=["exec-1"],
    )
    unknown = summarise_workflow_cost(
        [_attempt(cost_usd=None)],
        is_mock=False,
        execution_ids=["exec-1"],
    )

    assert mixed.total.amount_text() == "1.00"
    assert mixed.unsuccessful.state == "unknown"
    assert unknown.total.state == "unknown"
    assert unknown.total.amount_text() is None


def test_mock_run_is_zero_even_when_attempt_rows_exist() -> None:
    summary = summarise_workflow_cost(
        [_attempt(cost_usd=Decimal("9.00"))],
        is_mock=True,
        execution_ids=["exec-1"],
    )

    assert summary.total.amount_text() == "0.00"
    assert summary.figure_for_execution("exec-1").amount_text() == "0.00"


def test_figure_for_execution_rejects_an_unknown_id() -> None:
    summary = summarise_workflow_cost([], is_mock=False, execution_ids=["exec-1"])

    with pytest.raises(KeyError):
        summary.figure_for_execution("missing")
