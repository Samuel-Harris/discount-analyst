"""Tests for terminal run option helpers."""

import pytest
from pydantic import BaseModel
from pydantic_ai.capabilities.abstract import AbstractCapability

from common.config import load_settings, settings
from discount_analyst.agents.common import agent_factory as agent_factory_module
from discount_analyst.agents.common.agent_factory import AgentSpec, create_agent
from discount_analyst.agents.common.agent_names import AgentName
from discount_analyst.agents.common.terminal_run import (
    terminal_run_options,
)
from discount_analyst.config.ai_models_config import AIModelsConfig, ModelName
from discount_analyst.integrations.terminal import Terminal


class _MinimalOutput(BaseModel):
    value: int = 1


def _capability_tree_contains_terminal(root: AbstractCapability[None]) -> bool:
    found = False

    def visitor(cap: AbstractCapability[None]) -> None:
        nonlocal found
        if isinstance(cap, Terminal):
            found = True

    root.apply(visitor)
    return found


def test_default_terminal_follows_settings_for_interpretation_agents(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        agent_factory_module,
        "app_settings",
        settings.model_copy(update={"use_terminal": True}),
    )
    spec = AgentSpec(
        name=AgentName.STRATEGIST,
        output_type=_MinimalOutput,
        system_prompt="test",
    )
    terminal = terminal_run_options(
        agent_factory_module.app_settings,
        enabled=True,
    ).bind_session_id()
    agent = create_agent(
        spec=spec,
        ai_models_config=AIModelsConfig(model_name=ModelName.GPT_5_1),
        enable_web_research_tools=False,
        use_mcp_financial_data=False,
        terminal=terminal,
    )
    assert _capability_tree_contains_terminal(agent.root_capability)


def test_default_terminal_off_when_settings_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DASHBOARD_USE_TERMINAL", "false")
    cfg = load_settings()
    opts = terminal_run_options(cfg)
    assert opts.enabled is False


def test_terminal_run_options_respects_explicit_enabled() -> None:
    opts = terminal_run_options(settings, enabled=False, session_id="sid")
    assert opts.enabled is False
    assert opts.session_id == "sid"
