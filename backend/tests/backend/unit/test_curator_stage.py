"""Unit tests for the dashboard Curator pipeline stage."""

from __future__ import annotations

from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from discount_analyst.adapters.orchestration.llm_config import pipeline_llm_config
from discount_analyst.adapters.orchestration.stages.curator_stage import CuratorStage
from discount_analyst.adapters.persistence.models import AgentNameDb
from discount_analyst.adapters.simulation import mock_outputs
from discount_analyst.agents.curator.schema import CuratorInput
from discount_analyst.config.testing_settings import dashboard_settings_for_tests
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
        result = await CuratorStage()._run_curator_agent(
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
    assert run_with_terminal.await_args.kwargs["settings"] is settings
    assert run_with_terminal.await_args.kwargs["session_id"] == "curator-exec-1"
    assert callable(run_with_terminal.await_args.kwargs["build_agent"])
