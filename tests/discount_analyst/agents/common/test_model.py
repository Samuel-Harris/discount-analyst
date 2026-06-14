from types import SimpleNamespace
from typing import Any

import pytest

from discount_analyst.agents.common import model as model_module
from discount_analyst.config.ai_models_config import AIModelsConfig
from discount_analyst.models.model_name import ModelName


def test_create_deepseek_model_requires_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(model_module, "settings", SimpleNamespace(deepseek=None))

    with pytest.raises(ValueError, match="DEEPSEEK__API_KEY"):
        model_module.create_model_from_config(
            AIModelsConfig(model_name=ModelName.DEEPSEEK_V4_PRO).model
        )


def test_create_deepseek_model_uses_deepseek_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created_clients: list[float | None] = []
    created_providers: list[Any] = []

    class FakeOpenAIChatModel:
        def __init__(self, model_name: str, *, provider: Any) -> None:
            self.model_name = model_name
            self.provider = provider

    class FakeDeepSeekProvider:
        def __init__(self, *, api_key: str, http_client: object) -> None:
            self.api_key = api_key
            self.http_client = http_client
            created_providers.append(self)

    def fake_rate_limit_client(*, timeout: float | None = None) -> object:
        created_clients.append(timeout)
        return object()

    monkeypatch.setattr(
        model_module,
        "settings",
        SimpleNamespace(deepseek=SimpleNamespace(api_key="test-deepseek-key")),
    )
    monkeypatch.setattr(model_module, "OpenAIChatModel", FakeOpenAIChatModel)
    monkeypatch.setattr(model_module, "DeepSeekProvider", FakeDeepSeekProvider)
    monkeypatch.setattr(
        model_module, "create_rate_limit_client", fake_rate_limit_client
    )

    created_model = model_module.create_model_from_config(
        AIModelsConfig(model_name=ModelName.DEEPSEEK_V4_PRO).model
    )

    assert isinstance(created_model, FakeOpenAIChatModel)
    assert created_model.model_name == "deepseek-v4-pro"
    assert created_providers[0].api_key == "test-deepseek-key"
    assert created_model.provider is created_providers[0]
    assert created_clients == [1200]
