"""Unit tests for the terminal integration (orchestrator HTTP client)."""

from __future__ import annotations

import json
from collections.abc import Callable

import httpx
import pytest
from pydantic import BaseModel
from pydantic_ai.capabilities.abstract import AbstractCapability

from discount_analyst.agents.common.agent_factory import AgentSpec, create_agent
from discount_analyst.agents.common.terminal_run import (
    TerminalRunOptions,
    terminal_run_options,
)
from common.config import settings
from discount_analyst.agents.common.agent_names import AgentName
from discount_analyst.config.ai_models_config import AIModelsConfig, ModelName
from discount_analyst.integrations.terminal import (
    Terminal,
    TerminalLimits,
    TerminalSessionState,
    delete_terminal_session,
    execute_terminal_command,
    format_terminal_exec_response,
)


def _client_factory(
    handler: Callable[[httpx.Request], httpx.Response],
) -> type[httpx.AsyncClient]:
    """Build an AsyncClient subclass that always uses the given mock transport."""

    class _MockedAsyncClient(httpx.AsyncClient):
        def __init__(self, *args: object, **kwargs: object) -> None:
            kwargs["transport"] = httpx.MockTransport(handler)
            super().__init__(*args, **kwargs)

    return _MockedAsyncClient


@pytest.mark.anyio
async def test_delete_terminal_session_ignores_404(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append((request.method, str(request.url)))
        return httpx.Response(404)

    monkeypatch.setattr(
        "discount_analyst.integrations.terminal.httpx.AsyncClient",
        _client_factory(handler),
    )
    await delete_terminal_session("http://example.invalid", "sid-1")

    assert ("DELETE", "http://example.invalid/sessions/sid-1") in calls


def test_format_terminal_exec_response_includes_truncation_note() -> None:
    text = format_terminal_exec_response(
        {"exit_code": 1, "stdout": "a", "stderr": "b", "truncated": True}
    )
    assert "exit_code: 1" in text
    assert "truncated" in text


@pytest.mark.anyio
async def test_execute_terminal_command_happy_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session_post_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal session_post_count
        path = request.url.path
        if request.method == "POST" and path == "/sessions":
            session_post_count += 1
            body = json.loads(request.content.decode())
            assert body["session_id"] == "exec-test"
            return httpx.Response(
                200,
                json={
                    "session_id": "exec-test",
                    "container_id": "abc",
                    "container_name": "da-term-exec-test",
                },
            )
        if request.method == "POST" and path.endswith("/exec"):
            body = json.loads(request.content.decode())
            assert body["command"] in ("echo hi", "echo again")
            return httpx.Response(
                200,
                json={
                    "exit_code": 0,
                    "stdout": f"{body['command']}\n",
                    "stderr": "",
                    "truncated": False,
                },
            )
        return httpx.Response(500, text="unexpected")

    monkeypatch.setattr(
        "discount_analyst.integrations.terminal.httpx.AsyncClient",
        _client_factory(handler),
    )

    state = TerminalSessionState()
    out = await execute_terminal_command(
        service_url="http://orchestrator",
        limits=TerminalLimits(command_timeout_s=30, max_output_bytes=1024),
        session_id="exec-test",
        command="echo hi",
        session_state=state,
    )
    assert "exit_code: 0" in out
    assert "hi" in out
    assert session_post_count == 1
    # Second call reuses session
    await execute_terminal_command(
        service_url="http://orchestrator",
        limits=TerminalLimits(command_timeout_s=30, max_output_bytes=1024),
        session_id="exec-test",
        command="echo again",
        session_state=state,
    )
    assert session_post_count == 1


class _MinimalOutput(BaseModel):
    value: int = 1


def _capability_tree_contains_terminal(root: AbstractCapability[None]) -> bool:
    found_terminal = False

    def visitor(cap: AbstractCapability[None]) -> None:
        nonlocal found_terminal
        if isinstance(cap, Terminal):
            found_terminal = True

    root.apply(visitor)
    return found_terminal


def test_create_agent_with_terminal_includes_terminal_capability() -> None:
    spec = AgentSpec(
        name=AgentName.STRATEGIST,
        output_type=_MinimalOutput,
        system_prompt="test",
    )
    with_terminal = create_agent(
        spec=spec,
        ai_models_config=AIModelsConfig(model_name=ModelName.GPT_5_1),
        enable_web_research_tools=False,
        use_mcp_financial_data=False,
        terminal=terminal_run_options(settings, enabled=True).bind_session_id(),
    )
    without_terminal = create_agent(
        spec=spec,
        ai_models_config=AIModelsConfig(model_name=ModelName.GPT_5_1),
        enable_web_research_tools=False,
        use_mcp_financial_data=False,
        terminal=TerminalRunOptions(
            enabled=False,
            runtime=terminal_run_options(settings).runtime,
        ),
    )
    assert _capability_tree_contains_terminal(with_terminal.root_capability)
    assert not _capability_tree_contains_terminal(without_terminal.root_capability)


@pytest.mark.docker
@pytest.mark.anyio
async def test_orchestrator_sandbox_exec_integration() -> None:
    """Optional: requires Docker, sandbox image, and orchestrator on localhost:8001."""
    import os
    import shutil

    if shutil.which("docker") is None:
        pytest.skip("docker CLI not available")

    base = os.environ.get("TERMINAL_SERVICE_URL", "http://127.0.0.1:8001").rstrip("/")
    session_id = "pytest-terminal-integration"

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            health = await client.get(f"{base}/health")
            health.raise_for_status()
        except httpx.HTTPError as exc:
            pytest.skip(f"agent-terminal not reachable at {base}: {exc}")

        create = await client.post(
            f"{base}/sessions",
            json={"session_id": session_id},
        )
        if create.status_code >= 500:
            pytest.skip(f"orchestrator could not create sandbox: {create.text}")
        create.raise_for_status()

        exec_resp = await client.post(
            f"{base}/sessions/{session_id}/exec",
            json={"command": 'python -c "import pandas; print(pandas.__version__)"'},
        )
        exec_resp.raise_for_status()
        payload = exec_resp.json()
        assert payload["exit_code"] == 0
        assert payload["stdout"].strip()

        delete = await client.delete(f"{base}/sessions/{session_id}")
        assert delete.status_code in (204, 404)
