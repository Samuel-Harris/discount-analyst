from types import SimpleNamespace
from typing import Any

import pytest
from pydantic_ai.models import Model
from pydantic_ai.models.openai import OpenAIResponsesModel

import discount_analyst.config.ai_models_config as config_module
from discount_analyst.config.ai_models_config import AdmittedModel, AIModelsConfig
from discount_analyst.config.model_gate import process_model_gate
from discount_analyst.domain.model_selection.model_name import ModelName


def test_create_deepseek_model_requires_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(config_module, "settings", SimpleNamespace(deepseek=None))

    with pytest.raises(ValueError, match="DEEPSEEK__API_KEY"):
        AIModelsConfig(
            model_name=ModelName.DEEPSEEK_V4_PRO
        ).pydantic_ai_model.to_model()


def test_create_deepseek_model_uses_deepseek_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created_clients: list[float | None] = []
    created_providers: list[Any] = []

    class FakeOpenAIChatModel(Model):
        def __init__(self, model_name: str, *, provider: Any) -> None:
            super().__init__()
            self._model_name = model_name
            self._provider = provider

        @property
        def model_name(self) -> str:
            return self._model_name

        @property
        def system(self) -> str:
            return "deepseek"

        @property
        def provider(self) -> Any:
            return self._provider

        async def request(
            self,
            messages: list[Any],
            model_settings: Any,
            model_request_parameters: Any,
        ) -> Any:
            raise NotImplementedError

    class FakeDeepSeekProvider:
        def __init__(self, *, api_key: str, http_client: object) -> None:
            self.api_key = api_key
            self.http_client = http_client
            created_providers.append(self)

    def fake_rate_limit_client(*, timeout: float | None = None) -> object:
        created_clients.append(timeout)
        return object()

    monkeypatch.setattr(
        config_module,
        "settings",
        SimpleNamespace(deepseek=SimpleNamespace(api_key="test-deepseek-key")),
    )
    monkeypatch.setattr(config_module, "OpenAIChatModel", FakeOpenAIChatModel)
    monkeypatch.setattr(config_module, "DeepSeekProvider", FakeDeepSeekProvider)
    monkeypatch.setattr(
        config_module, "create_rate_limit_client", fake_rate_limit_client
    )

    created_model = AIModelsConfig(
        model_name=ModelName.DEEPSEEK_V4_PRO
    ).pydantic_ai_model.to_model()

    assert isinstance(created_model, AdmittedModel)
    assert created_model.gate is process_model_gate("deepseek-v4-pro", 1)
    assert created_model.gate.max_running == 1
    provider_model = created_model.wrapped
    assert isinstance(provider_model, FakeOpenAIChatModel)
    assert provider_model.model_name == "deepseek-v4-pro"
    assert created_providers[0].api_key == "test-deepseek-key"
    assert provider_model.provider is created_providers[0]
    assert created_clients == [1200]


def test_sol_responses_model_sends_pro_reasoning_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        config_module,
        "settings",
        SimpleNamespace(openai=SimpleNamespace(api_key="test-openai-key")),
    )

    created_model = AIModelsConfig(
        model_name=ModelName.GPT_6_1_SOL
    ).pydantic_ai_model.to_model()

    assert isinstance(created_model, AdmittedModel)
    provider_model = created_model.wrapped
    assert isinstance(provider_model, OpenAIResponsesModel)
    assert (
        provider_model.profile.get("openai_responses_supports_reasoning_mode") is True
    )
