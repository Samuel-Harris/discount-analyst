"""Unit tests for the dashboard Curator pipeline stage."""

from __future__ import annotations

from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from discount_analyst.adapters.orchestration.llm_config import pipeline_llm_config
from discount_analyst.adapters.orchestration.stages.curator_stage import (
    CuratorStage,
    load_completed_lane_bundles,
    load_dashboard_portfolio_snapshot,
    persist_completed_curator_execution,
    update_agent_execution,
)
from discount_analyst.adapters.orchestration.stages.curator_stage import (
    _curator_execution_id_and_status,  # pyright: ignore[reportPrivateUsage]
)
from discount_analyst.adapters.persistence.crud.workflow_runs import (
    list_ticker_runs_for_workflow,
)
from discount_analyst.adapters.persistence.models import (
    AgentNameDb,
    WorkflowRunStatusDb,
)
from discount_analyst.adapters.simulation import mock_outputs
from discount_analyst.agents.curator.schema import (
    CuratorInput,
    CuratorProposal,
    ProposedCash,
    ProposedPosition,
)
from discount_analyst.application.allocations.assemble import valued_lane_bundle
from discount_analyst.application.decisions.builders import build_appraised_decision
from discount_analyst.config.testing_settings import dashboard_settings_for_tests
from discount_analyst.domain.allocations.invariants import AllocationInvariantError
from discount_analyst.domain.allocations.snapshot import CurrentPortfolioSnapshot


def _empty_curator_input() -> CuratorInput:
    return CuratorInput(
        allocation_date=date(2026, 8, 30),
        snapshot=CurrentPortfolioSnapshot(
            as_of=date(2026, 8, 30),
            positions=(),
            cash_weight_pct=100.0,
        ),
        lanes=(),
    )


@pytest.mark.asyncio
async def test_curator_stage_non_mock_path_uses_run_agent_with_terminal() -> None:
    settings = dashboard_settings_for_tests()
    curator_input = _empty_curator_input()
    proposal = mock_outputs.mock_curator_proposal(curator_input)
    fake_outcome = SimpleNamespace(output=proposal, all_messages=[object()])

    with patch(
        "discount_analyst.adapters.orchestration.stages.curator_stage.run_agent_with_terminal",
        new=AsyncMock(return_value=fake_outcome),
    ) as run_with_terminal:
        result = await CuratorStage()._run_curator_agent(  # pyright: ignore[reportPrivateUsage]
            curator_input=curator_input,
            is_mock=False,
            llm=pipeline_llm_config(
                settings, agent_name=AgentNameDb.CURATOR, is_mock=False
            ),
            settings=settings,
            session_id="curator-exec-1",
        )

    assert result.proposal is proposal
    assert result.messages == fake_outcome.all_messages
    assert run_with_terminal.await_args is not None
    assert run_with_terminal.await_args.kwargs["settings"] is settings
    assert run_with_terminal.await_args.kwargs["session_id"] == "curator-exec-1"
    assert callable(run_with_terminal.await_args.kwargs["build_agent"])


class _RecordingHost:
    def __init__(self, valued: tuple[object, ...], dqr: tuple[object, ...]) -> None:
        self.bundles = (valued, dqr)
        self.settings = dashboard_settings_for_tests()
        self.updates: list[dict[str, object]] = []
        self.persisted = False

    async def recompute(self, workflow_run_id: str) -> None:
        del workflow_run_id

    async def db(self, fn: object, *args: object, **kwargs: object) -> object:
        del args
        if fn is _curator_execution_id_and_status:
            return ("exec-1", "pending")
        if fn is list_ticker_runs_for_workflow:
            return [{"status": WorkflowRunStatusDb.COMPLETED.value}]
        if fn is load_dashboard_portfolio_snapshot:
            return CurrentPortfolioSnapshot(
                as_of=date(2026, 9, 7),
                positions=(),
                cash_weight_pct=100.0,
            )
        if fn is load_completed_lane_bundles:
            return self.bundles
        if fn is update_agent_execution:
            self.updates.append(dict(kwargs))
            return None
        if fn is persist_completed_curator_execution:
            self.persisted = True
            return None
        msg = f"Unexpected db call {fn!r}"
        raise AssertionError(msg)


def _hurdle_breach_bundle() -> object:
    candidate = mock_outputs.mock_surveyor_candidate(ticker="THX.L")
    output = mock_outputs.mock_appraiser_output(candidate)
    distribution = output.valuation_distribution.model_copy(
        update={
            "current_share_price": 100.0,
            "expected_intrinsic_value": 104.0,
            "p10_intrinsic_value": 16.0,
        }
    )
    decision = build_appraised_decision(
        candidate.to_lane_context(),
        is_existing_position=False,
        decision_date="2026-09-07",
    )
    return valued_lane_bundle(
        source_run_id="run-thx",
        decision=decision,
        sector=candidate.sector,
        industry=candidate.industry,
        market_cap_local=candidate.market_cap_local,
        market_cap_currency="GBP",
        deep_research=mock_outputs.mock_deep_research(candidate),
        thesis=mock_outputs.mock_thesis(candidate),
        evaluation=mock_outputs.mock_rating_table_gate_evaluation(candidate),
        appraiser_output=output.model_copy(
            update={"valuation_distribution": distribution}
        ),
    )


@pytest.mark.asyncio
async def test_hurdle_breach_fails_execution_without_persisting_allocation() -> None:
    bundle = _hurdle_breach_bundle()
    host = _RecordingHost((bundle,), ())
    proposal = CuratorProposal(
        allocation_date=date.today(),
        positions=(
            ProposedPosition(
                ticker="THX.L",
                target_weight_pct=4.0,
                acceptable_weight_low_pct=4.0,
                acceptable_weight_high_pct=4.0,
                rationale="New money that cannot clear the hurdle.",
            ),
        ),
        cash=ProposedCash(
            target_weight_pct=96.0,
            acceptable_weight_low_pct=96.0,
            acceptable_weight_high_pct=96.0,
            rationale="Residual cash.",
        ),
        shared_risk_clusters=(),
        portfolio_rationale="Would have bought THX.L.",
    )

    async def fake_run(self: CuratorStage, **kwargs: object) -> SimpleNamespace:
        del self, kwargs
        return SimpleNamespace(proposal=proposal, messages=None, messages_json=None)

    with (
        patch.object(CuratorStage, "_run_curator_agent", fake_run),
        pytest.raises(AllocationInvariantError, match="THX.L"),
    ):
        await CuratorStage().run(host, workflow_run_id="wf-1", is_mock=True)

    assert host.persisted is False
    failed = [update for update in host.updates if update.get("status") == "failed"]
    assert failed
    assert "THX.L" in str(failed[-1]["error_message"])
