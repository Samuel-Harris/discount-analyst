from types import SimpleNamespace

import pytest
from pydantic_ai.models.test import TestModel
from pydantic_ai.tools import Tool
from pydantic_ai_harness.tool_output_limits import Truncate

from discount_analyst.agents.runtime import agent_factory
from discount_analyst.agents.runtime.agent_factory import (
    TOOL_OUTPUT_CHAR_LIMIT,
    TOOL_OUTPUT_LIMITS,
    AgentSpec,
    create_agent,
    create_web_research_tooling,
)
from discount_analyst.agents.runtime.agent_names import AgentName
from discount_analyst.agents.runtime.tool_descriptions import AGENT_TOOL_DESCRIPTIONS
from discount_analyst.agents.common_prompts.current_date import format_current_date_line
from discount_analyst.agents.sentinel import sentinel as sentinel_module
from discount_analyst.agents.sentinel.sentinel import create_sentinel_agent
from discount_analyst.agents.strategist import strategist as strategist_module
from discount_analyst.agents.strategist.strategist import create_strategist_agent
from discount_analyst.config.ai_models_config import (
    AIModelConfig,
    AIModelsConfig,
)
from discount_analyst.config.provider_features import Provider
from discount_analyst.domain.model_selection.model_name import ModelName


def test_create_web_research_tooling_uses_pydantic_web_capabilities(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created_capabilities: list[tuple[str, bool, object]] = []
    search_tool = Tool(lambda query: None, name="duckduckgo_search")

    class FakeWebSearch:
        def __init__(self, *, native: bool, local: object) -> None:
            created_capabilities.append(("web_search", native, local))

    class FakeWebFetch:
        def __init__(self, *, native: bool, local: object) -> None:
            created_capabilities.append(("web_fetch", native, local))

    monkeypatch.setattr(agent_factory, "WebSearch", FakeWebSearch)
    monkeypatch.setattr(agent_factory, "WebFetch", FakeWebFetch)
    monkeypatch.setattr(
        agent_factory,
        "create_bounded_duckduckgo_search_tool",
        lambda: search_tool,
    )

    tooling = create_web_research_tooling(
        agent_name=AgentName.SURVEYOR,
        use_perplexity=False,
        provider=Provider.OPENAI,
    )

    assert not tooling.toolsets
    assert len(tooling.capabilities) == 2
    assert created_capabilities == [
        ("web_search", True, search_tool),
        ("web_fetch", True, True),
    ]


def test_create_web_research_tooling_uses_text_only_fetch_for_deepseek(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created_capabilities: list[tuple[str, bool, object]] = []
    search_tool = Tool(lambda query: None, name="duckduckgo_search")
    fake_tool = Tool(lambda url: None, name="web_fetch")

    class FakeWebSearch:
        def __init__(self, *, native: bool, local: object) -> None:
            created_capabilities.append(("web_search", native, local))

    class FakeWebFetch:
        def __init__(self, *, native: bool, local: object) -> None:
            created_capabilities.append(("web_fetch", native, local))

    monkeypatch.setattr(agent_factory, "WebSearch", FakeWebSearch)
    monkeypatch.setattr(agent_factory, "WebFetch", FakeWebFetch)
    monkeypatch.setattr(
        agent_factory,
        "create_bounded_duckduckgo_search_tool",
        lambda: search_tool,
    )
    monkeypatch.setattr(
        agent_factory,
        "create_text_only_web_fetch_tool",
        lambda: fake_tool,
    )

    tooling = create_web_research_tooling(
        agent_name=AgentName.SURVEYOR,
        use_perplexity=False,
        provider=Provider.DEEPSEEK,
    )

    assert not tooling.toolsets
    assert len(tooling.capabilities) == 2
    assert created_capabilities == [
        ("web_search", True, search_tool),
        ("web_fetch", True, fake_tool),
    ]


def test_create_agent_prepends_current_date_to_system_prompt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, str] = {}

    def fake_create_model_from_config(_config: AIModelConfig) -> TestModel:
        return TestModel()

    def fake_agent(*, system_prompt: str, **kwargs: object) -> SimpleNamespace:
        captured["system_prompt"] = system_prompt
        return SimpleNamespace(name=kwargs.get("name"))

    monkeypatch.setattr(
        agent_factory,
        "create_model_from_config",
        fake_create_model_from_config,
    )
    monkeypatch.setattr(agent_factory, "Agent", fake_agent)

    agent = create_agent(
        spec=AgentSpec(name=AgentName.SURVEYOR, output_type=str, system_prompt="test"),
        ai_models_config=AIModelsConfig(model_name=ModelName.DEEPSEEK_V4_PRO),
        use_mcp_financial_data=False,
    )

    assert agent.name == AgentName.SURVEYOR
    assert captured["system_prompt"].startswith(format_current_date_line())
    assert captured["system_prompt"].endswith("test")


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


def test_create_agent_attaches_always_on_tooling(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fx_toolset = object()
    captured: dict[str, object] = {}

    def fake_create_model_from_config(_config: AIModelConfig) -> TestModel:
        return TestModel()

    def fake_agent(**kwargs: object) -> SimpleNamespace:
        captured["toolsets"] = kwargs.get("toolsets")
        captured["capabilities"] = kwargs.get("capabilities")
        return SimpleNamespace(name=kwargs.get("name"))

    monkeypatch.setattr(agent_factory, "create_frankfurter_toolset", lambda: fx_toolset)
    monkeypatch.setattr(
        agent_factory,
        "create_model_from_config",
        fake_create_model_from_config,
    )
    monkeypatch.setattr(agent_factory, "Agent", fake_agent)

    create_agent(
        spec=AgentSpec(name=AgentName.SURVEYOR, output_type=str, system_prompt="test"),
        ai_models_config=AIModelsConfig(model_name=ModelName.DEEPSEEK_V4_PRO),
        enable_web_research_tools=False,
        use_mcp_financial_data=False,
    )

    assert captured["toolsets"] == [fx_toolset]
    assert captured["capabilities"] == [
        TOOL_OUTPUT_LIMITS,
        agent_factory.INFALLIBLE_TOOL_EXECUTION,
    ]
    bands = list(TOOL_OUTPUT_LIMITS.bands)
    assert len(bands) == 1
    assert bands[0].over == TOOL_OUTPUT_CHAR_LIMIT
    assert isinstance(bands[0].action, Truncate)
    assert bands[0].action.max_chars == TOOL_OUTPUT_CHAR_LIMIT


def test_create_strategist_agent_does_not_force_web_mcp_off(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_create_agent(**kwargs: object) -> SimpleNamespace:
        captured.update(kwargs)
        return SimpleNamespace()

    monkeypatch.setattr(strategist_module, "create_agent", fake_create_agent)
    create_strategist_agent(AIModelsConfig(model_name=ModelName.DEEPSEEK_V4_PRO))

    assert captured.get("enable_web_research_tools", True) is True
    assert captured["use_perplexity"] is False
    assert captured["use_mcp_financial_data"] is True


def test_create_strategist_agent_forwards_web_mcp_flags(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_create_agent(**kwargs: object) -> SimpleNamespace:
        captured.update(kwargs)
        return SimpleNamespace()

    monkeypatch.setattr(strategist_module, "create_agent", fake_create_agent)
    create_strategist_agent(
        AIModelsConfig(model_name=ModelName.DEEPSEEK_V4_PRO),
        use_perplexity=True,
        use_mcp_financial_data=False,
    )

    assert captured["use_perplexity"] is True
    assert captured["use_mcp_financial_data"] is False


def test_create_sentinel_agent_is_interpretation_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_create_agent(**kwargs: object) -> SimpleNamespace:
        captured.update(kwargs)
        return SimpleNamespace()

    monkeypatch.setattr(sentinel_module, "create_agent", fake_create_agent)
    create_sentinel_agent(AIModelsConfig(model_name=ModelName.DEEPSEEK_V4_PRO))

    assert captured["enable_web_research_tools"] is False
    assert captured["use_perplexity"] is False
    assert captured["use_mcp_financial_data"] is False
    terminal = captured["terminal"]
    assert getattr(terminal, "enabled") is False


def test_perplexity_descriptions_cover_every_agent() -> None:
    assert set(AGENT_TOOL_DESCRIPTIONS) == set(AgentName)
