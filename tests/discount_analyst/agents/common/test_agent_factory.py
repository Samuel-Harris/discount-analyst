import pytest
from pydantic_ai.models.test import TestModel

from discount_analyst.agents.common import agent_factory
from discount_analyst.agents.common.agent_factory import (
    AgentSpec,
    create_agent,
    create_web_research_tooling,
)
from discount_analyst.agents.common.agent_names import AgentName
from discount_analyst.config.ai_models_config import (
    AIModelConfig,
    AIModelsConfig,
    ModelName,
)


def test_create_web_research_tooling_uses_pydantic_web_capabilities(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created_capabilities: list[tuple[str, bool, object]] = []

    class FakeWebSearch:
        def __init__(self, *, native: bool, local: object) -> None:
            created_capabilities.append(("web_search", native, local))

    class FakeWebFetch:
        def __init__(self, *, native: bool, local: object) -> None:
            created_capabilities.append(("web_fetch", native, local))

    monkeypatch.setattr(agent_factory, "WebSearch", FakeWebSearch)
    monkeypatch.setattr(agent_factory, "WebFetch", FakeWebFetch)

    tooling = create_web_research_tooling(
        agent_name=AgentName.SURVEYOR,
        use_perplexity=False,
    )

    assert not tooling.toolsets
    assert len(tooling.capabilities) == 2
    assert created_capabilities == [
        ("web_search", True, "duckduckgo"),
        ("web_fetch", True, True),
    ]


def test_create_agent_accepts_deepseek_web_research_tooling(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_create_model_from_config(_config: AIModelConfig) -> TestModel:
        return TestModel()

    monkeypatch.setattr(
        agent_factory,
        "create_model_from_config",
        fake_create_model_from_config,
    )

    agent = create_agent(
        spec=AgentSpec(name=AgentName.SURVEYOR, output_type=str, system_prompt="test"),
        ai_models_config=AIModelsConfig(model_name=ModelName.DEEPSEEK_V4_PRO),
        use_mcp_financial_data=False,
    )

    assert agent.name == AgentName.SURVEYOR
