#!/usr/bin/env python3
"""End-to-end verification for the agent-terminal orchestrator and sandbox.

Run from repo root (orchestrator must be reachable at TERMINAL_SERVICE_URL):

    TERMINAL_SERVICE_URL=http://agent-terminal:8001 uv run python scripts/verify_agent_terminal.py

Inside Compose:

    docker compose exec -T backend uv run python scripts/verify_agent_terminal.py
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from dataclasses import dataclass, field

import httpx
from rich.console import Console
from rich.table import Table

from discount_analyst.integrations.terminal import (
    TerminalLimits,
    TerminalSessionState,
    delete_terminal_session,
    execute_terminal_command,
    format_terminal_exec_response,
)

console = Console()


@dataclass
class PhaseResult:
    name: str
    passed: bool
    detail: str = ""


@dataclass
class VerifyState:
    base_url: str
    session_id: str
    results: list[PhaseResult] = field(default_factory=list)
    host_pydantic: str | None = None

    def ok(self, name: str, detail: str = "") -> None:
        self.results.append(PhaseResult(name, True, detail))

    def fail(self, name: str, detail: str) -> None:
        self.results.append(PhaseResult(name, False, detail))


def _client(timeout: float = 120.0) -> httpx.Client:
    return httpx.Client(base_url=state.base_url, timeout=timeout)


state: VerifyState


def phase0_preconditions(s: VerifyState) -> bool:
    """Image + health + session create."""
    with _client() as client:
        try:
            health = client.get("/health")
            if health.status_code != 200 or health.json().get("status") != "ok":
                s.fail("health", f"unexpected: {health.status_code} {health.text}")
                return False
            s.ok("health", health.text.strip())
        except httpx.HTTPError as exc:
            s.fail("health", str(exc))
            return False

        create = client.post("/sessions", json={"session_id": s.session_id})
        if create.status_code >= 500:
            s.fail(
                "create_session",
                f"{create.status_code}: {create.text[:500]} "
                "(try DOCKER_RUNTIME=runc on orchestrator if runsc fails)",
            )
            return False
        create.raise_for_status()
        body = create.json()
        s.ok("create_session", f"container={body.get('container_name')}")
    return True


def phase1_api_smoke(s: VerifyState) -> bool:
    all_ok = True
    with _client() as client:
        # shell sanity
        r = client.post(
            f"/sessions/{s.session_id}/exec",
            json={"command": "echo ok && pwd && python --version"},
        )
        if r.status_code != 200:
            s.fail("shell_sanity", f"HTTP {r.status_code}: {r.text[:300]}")
            all_ok = False
        else:
            payload = r.json()
            if payload["exit_code"] != 0 or "ok" not in payload["stdout"]:
                s.fail("shell_sanity", json.dumps(payload)[:400])
                all_ok = False
            elif "3.14" not in payload["stdout"]:
                s.fail("shell_sanity", f"expected Python 3.14.x: {payload['stdout']}")
                all_ok = False
            else:
                s.ok("shell_sanity", payload["stdout"].strip()[:120])

        # persistence
        client.post(
            f"/sessions/{s.session_id}/exec",
            json={"command": "echo step1 > /tmp/agent_probe.txt"},
        ).raise_for_status()
        r2 = client.post(
            f"/sessions/{s.session_id}/exec",
            json={
                "command": (
                    "cat /tmp/agent_probe.txt && echo step2 >> /tmp/agent_probe.txt "
                    "&& wc -l /tmp/agent_probe.txt"
                )
            },
        )
        r2.raise_for_status()
        p2 = r2.json()
        if (
            p2["exit_code"] != 0
            or "step1" not in p2["stdout"]
            or "2" not in p2["stdout"]
        ):
            s.fail("filesystem_persistence", json.dumps(p2)[:400])
            all_ok = False
        else:
            s.ok("filesystem_persistence", p2["stdout"].strip()[:80])

        # failure path
        r3 = client.post(
            f"/sessions/{s.session_id}/exec",
            json={"command": "exit 42"},
        )
        r3.raise_for_status()
        if r3.json()["exit_code"] != 42:
            s.fail("exit_code_propagation", str(r3.json()))
            all_ok = False
        else:
            s.ok("exit_code_propagation", "exit_code=42")

        # formatted response shape
        formatted = format_terminal_exec_response(r3.json())
        if "--- stdout ---" not in formatted or "exit_code:" not in formatted:
            s.fail("response_format", formatted[:200])
            all_ok = False
        else:
            s.ok("response_format", "format_terminal_exec_response OK")

    return all_ok


LIBRARY_MATRIX_SCRIPT = r"""
import json
import sys

def check(name, fn):
    try:
        result = fn()
        print(f"PASS {name}: {result}")
        return True
    except Exception as exc:
        print(f"FAIL {name}: {exc}", file=sys.stderr)
        return False

ok = True
ok &= check("pydantic", lambda: __import__("pydantic").__version__)
ok &= check("numpy", lambda: float(__import__("numpy").arange(3).sum()))
ok &= check("pandas", lambda: str(__import__("pandas").DataFrame({"x": [1, 2]}).shape))
ok &= check("scipy", lambda: round(float(__import__("scipy").stats.norm.ppf(0.975)), 4))
ok &= check("tabulate", lambda: __import__("tabulate").tabulate([["ticker", "price"], ["TEST", 1.0]], headers="firstrow")[:20])

import sympy as sp
g, r, n = sp.symbols("g r n", positive=True, real=True)
fcf, pv = sp.symbols("fcf pv", positive=True, real=True)
eq = sp.Eq(pv, fcf * (1 - (1 + g) ** n / (1 + r) ** n) / (r - g))
ok &= check("sympy", lambda: str(sp.solve(eq, pv)[0])[:40])

import statsmodels.api as sm
macro = sm.datasets.macrodata.load_pandas().data
ok &= check("statsmodels", lambda: f"rows={len(macro)}")

import pandas_datareader as pdr
ok &= check("pandas_datareader_import", lambda: pdr.__version__)
try:
    gdp = pdr.get_data_fred("GDP", start="2020-01-01")
    if gdp.empty:
        raise RuntimeError("FRED GDP series empty")
    ok &= check("pandas_datareader_fred", lambda: f"rows={len(gdp)}")
except Exception as exc:
    print(f"WARN pandas_datareader_fred: {exc} (network or FRED API; yfinance is primary)")

import yfinance as yf
hist = yf.Ticker("AAPL").history(period="5d")
if hist.empty or "Close" not in hist.columns:
    raise RuntimeError("yfinance returned empty history")
ok &= check("yfinance", lambda: f"closes={len(hist)} last={float(hist['Close'].iloc[-1]):.2f}")

if not ok:
    sys.exit(1)
print("MATRIX_OK")
"""


def _python_script_exec_command(script: str) -> str:
    """Run a multi-line Python script inside the sandbox via base64 (avoids shell quoting bugs)."""
    import base64

    encoded = base64.b64encode(script.encode()).decode()
    return (
        f'python -c "import base64; '
        f"exec(base64.b64decode('{encoded}').decode(), {{'__name__': '__main__'}})\""
    )


def phase2_library_matrix(s: VerifyState) -> bool:
    import subprocess

    host_ver = subprocess.run(
        [sys.executable, "-c", "import pydantic; print(pydantic.__version__)"],
        capture_output=True,
        text=True,
        check=True,
    )
    s.host_pydantic = host_ver.stdout.strip()

    cmd = _python_script_exec_command(LIBRARY_MATRIX_SCRIPT)
    with _client(timeout=300.0) as client:
        r = client.post(
            f"/sessions/{s.session_id}/exec",
            json={"command": cmd},
        )
        if r.status_code != 200:
            s.fail("library_matrix", f"HTTP {r.status_code}")
            return False
        payload = r.json()
        if payload["exit_code"] != 0:
            s.fail(
                "library_matrix",
                f"exit={payload['exit_code']} stderr={payload['stderr'][:500]} "
                f"stdout={payload['stdout'][:500]}",
            )
            return False
        if "MATRIX_OK" not in payload["stdout"]:
            s.fail("library_matrix", payload["stdout"][:800])
            return False

        # pydantic version from sandbox
        r2 = client.post(
            f"/sessions/{s.session_id}/exec",
            json={
                "command": 'python -c "import pydantic; print(pydantic.__version__)"'
            },
        )
        r2.raise_for_status()
        sandbox_ver = r2.json()["stdout"].strip().splitlines()[-1]
        if sandbox_ver != s.host_pydantic:
            s.fail(
                "pydantic_parity",
                f"host={s.host_pydantic} sandbox={sandbox_ver} "
                "(rebuild sandbox image after pyproject/uv.lock changes)",
            )
            return False
        s.ok("library_matrix", f"pydantic={sandbox_ver}")
    return True


async def phase3_python_client(s: VerifyState) -> bool:
    limits = TerminalLimits(command_timeout_s=300, max_output_bytes=2_097_152)
    session_state = TerminalSessionState()
    sid = f"{s.session_id}-client"
    try:
        out1 = await execute_terminal_command(
            service_url=s.base_url,
            limits=limits,
            session_id=sid,
            command="echo client1",
            session_state=session_state,
        )
        out2 = await execute_terminal_command(
            service_url=s.base_url,
            limits=limits,
            session_id=sid,
            command="echo client2",
            session_state=session_state,
        )
        if "client1" not in out1 or "client2" not in out2:
            s.fail("python_client", f"out1={out1[:100]} out2={out2[:100]}")
            return False
        if not session_state.ready:
            s.fail("python_client", "session_state.ready not set")
            return False
        s.ok("python_client", "execute_terminal_command x2 OK")
        await delete_terminal_session(s.base_url, sid)
        s.ok("delete_session", f"deleted {sid}")
        return True
    except Exception as exc:
        s.fail("python_client", str(exc))
        return False


def phase4_limits(s: VerifyState) -> bool:
    """Truncation + long pandas job (skip 400s timeout in quick verify)."""
    all_ok = True
    with _client(timeout=300.0) as client:
        # ~2.1MB output should truncate (default cap 2MB)
        r = client.post(
            f"/sessions/{s.session_id}/exec",
            json={"command": "python -c \"print('x' * (2 * 1024 * 1024 + 4096))\""},
        )
        r.raise_for_status()
        if not r.json().get("truncated"):
            s.fail("output_truncation", "expected truncated=true")
            all_ok = False
        else:
            s.ok("output_truncation", "truncated=true")

        r2 = client.post(
            f"/sessions/{s.session_id}/exec",
            json={
                "command": (
                    'python -c "import pandas as pd; import numpy as np; '
                    "df=pd.DataFrame({'v': np.random.randn(10000)}); "
                    "print(df['v'].rolling(20).mean().iloc[-1])\""
                )
            },
        )
        r2.raise_for_status()
        if r2.json()["exit_code"] != 0:
            s.fail("long_pandas", r2.json().get("stderr", "")[:300])
            all_ok = False
        else:
            s.ok("long_pandas", "10k rolling mean OK")
    return all_ok


SCENARIO_A_FETCH = """
import yfinance as yf
t = yf.Ticker("AAPL")
h = t.history(period="1y", interval="1mo")
h[["Close"]].to_csv("/tmp/prices.csv")
print(len(h))
"""

SCENARIO_A_TABLE = """
import pandas as pd
from tabulate import tabulate
df = pd.read_csv("/tmp/prices.csv", index_col=0, parse_dates=True)
ret = (df["Close"].iloc[-1] / df["Close"].iloc[0] - 1) * 100
print(tabulate([["AAPL", f"{ret:.2f}%"]], headers=["ticker", "12m_return"]))
"""

SCENARIO_B_SYMPY = """
import sympy as sp
r, n, fcf = sp.symbols("r n fcf")
pv = fcf * (1 - (1 + r) ** (-n)) / r
print(float(pv.subs({r: 0.1, n: 5, fcf: 100})))
"""

SCENARIO_B_NUMERIC = """
fcf, r, n = 100, 0.1, 5
pv = sum(fcf / (1 + r) ** t for t in range(1, n + 1))
print(pv)
"""

SCENARIO_B_PYDANTIC = """
from pydantic import BaseModel
class Assumptions(BaseModel):
    fcf: float
    r: float
print(Assumptions(fcf=100, r=0.1).model_dump_json())
"""


def phase5_scenarios(s: VerifyState) -> bool:
    all_ok = True
    sid = f"{s.session_id}-scenarios"
    with _client(timeout=300.0) as client:
        client.post("/sessions", json={"session_id": sid}).raise_for_status()

        # Scenario A
        r1 = client.post(
            f"/sessions/{sid}/exec",
            json={"command": _python_script_exec_command(SCENARIO_A_FETCH)},
        )
        r1.raise_for_status()
        p1 = r1.json()
        if p1["exit_code"] != 0 or not p1["stdout"].strip().isdigit():
            s.fail("scenario_a_fetch", json.dumps(p1)[:400])
            all_ok = False
        else:
            r2 = client.post(
                f"/sessions/{sid}/exec",
                json={"command": _python_script_exec_command(SCENARIO_A_TABLE)},
            )
            r2.raise_for_status()
            p2 = r2.json()
            r3 = client.post(
                f"/sessions/{sid}/exec",
                json={"command": "head -3 /tmp/prices.csv"},
            )
            r3.raise_for_status()
            if (
                p2["exit_code"] != 0
                or "AAPL" not in p2["stdout"]
                or "Close" not in r3.json()["stdout"]
            ):
                s.fail("scenario_a", f"p2={p2} p3={r3.json()}")
                all_ok = False
            else:
                s.ok("scenario_a_researcher", p2["stdout"].strip()[:80])

        # Scenario B
        b1 = client.post(
            f"/sessions/{sid}/exec",
            json={"command": _python_script_exec_command(SCENARIO_B_SYMPY)},
        )
        b1.raise_for_status()
        sym_val = float(b1.json()["stdout"].strip().split()[-1])
        b2 = client.post(
            f"/sessions/{sid}/exec",
            json={"command": _python_script_exec_command(SCENARIO_B_NUMERIC)},
        )
        b2.raise_for_status()
        num_val = float(b2.json()["stdout"].strip().split()[-1])
        b3 = client.post(
            f"/sessions/{sid}/exec",
            json={"command": _python_script_exec_command(SCENARIO_B_PYDANTIC)},
        )
        b3.raise_for_status()
        if abs(sym_val - num_val) > 0.01 or b3.json()["exit_code"] != 0:
            s.fail("scenario_b", f"sym={sym_val} num={num_val} b3={b3.json()}")
            all_ok = False
        else:
            s.ok("scenario_b_appraiser", f"PV sym≈num ({sym_val:.2f})")

        # Scenario C
        c1 = client.post(
            f"/sessions/{sid}/exec",
            json={
                "command": (
                    'python -c "import numpy as np, statsmodels.api as sm; '
                    "x=np.arange(20); y=2*x+1+np.random.randn(20)*0.1; "
                    'res=sm.OLS(y, sm.add_constant(x)).fit(); print(res.params[1])"'
                )
            },
        )
        c1.raise_for_status()
        c2 = client.post(
            f"/sessions/{sid}/exec",
            json={
                "command": (
                    'python -c "from scipy import stats; '
                    'print(round(stats.norm.interval(0.95, loc=0, scale=1)[1], 4))"'
                )
            },
        )
        c2.raise_for_status()
        if c1.json()["exit_code"] != 0 or c2.json()["exit_code"] != 0:
            s.fail("scenario_c", f"c1={c1.json()} c2={c2.json()}")
            all_ok = False
        else:
            s.ok("scenario_c_quant", "OLS + scipy interval OK")

        client.delete(f"/sessions/{sid}")

    return all_ok


def phase1_cleanup(s: VerifyState) -> bool:
    with _client() as client:
        r = client.delete(f"/sessions/{s.session_id}")
        if r.status_code not in (204, 404):
            s.fail("delete_session", f"HTTP {r.status_code}")
            return False
        s.ok("delete_main_session", "204")
        r2 = client.post(
            f"/sessions/{s.session_id}/exec",
            json={"command": "echo should_fail"},
        )
        if r2.status_code != 404:
            s.fail("post_delete_404", f"expected 404 got {r2.status_code}")
            return False
        s.ok("post_delete_404", "exec returns 404 after delete")
    return True


async def phase6_live_agent(s: VerifyState) -> bool:
    """Minimal agent with terminal_exec only (requires model API key)."""
    if os.environ.get("SKIP_TERMINAL_LIVE_AGENT", "").lower() in ("1", "true", "yes"):
        s.ok("live_agent", "skipped (SKIP_TERMINAL_LIVE_AGENT)")
        return True

    from pydantic import BaseModel

    from common.config import load_settings
    from discount_analyst.agents.common.agent_factory import AgentSpec, create_agent
    from discount_analyst.agents.common.agent_names import AgentName
    from discount_analyst.agents.common.streamed_agent_run import run_streamed_agent
    from discount_analyst.agents.common.terminal_run import terminal_run_options
    from discount_analyst.config.ai_models_config import AIModelsConfig, ModelName
    from pydantic_ai.usage import UsageLimits

    class _Echo(BaseModel):
        summary: str

    settings = load_settings()
    settings = settings.model_copy(
        update={
            "terminal_service_url": s.base_url,
            "use_terminal": True,
        }
    )
    terminal = terminal_run_options(
        settings, enabled=True, session_id=f"{s.session_id}-live"
    )
    spec = AgentSpec(
        name=AgentName.PROFILER,
        output_type=_Echo,
        system_prompt="You verify terminal_exec. Reply with a one-line summary.",
    )
    agent = create_agent(
        spec=spec,
        ai_models_config=AIModelsConfig(model_name=ModelName.GPT_5_1),
        enable_web_research_tools=False,
        use_mcp_financial_data=False,
        terminal=terminal,
    )
    prompt = (
        "Use terminal_exec exactly once with this command: "
        'python -c "import yfinance as yf; from tabulate import tabulate; '
        "h=yf.Ticker('AAPL').history(period='5d'); "
        "w=(h['Close'].iloc[-1]/h['Close'].iloc[0]-1)*100; "
        "print(tabulate([[\\'AAPL\\',f\\'{w:.2f}%\\']],headers=['ticker','5d_return']))\". "
        "Then set summary to the stdout from that command."
    )
    try:
        outcome = await run_streamed_agent(
            agent=agent,
            user_prompt=prompt,
            usage_limits=UsageLimits(request_limit=8, tool_calls_limit=4),
            terminal=terminal,
            run_settings=settings,
        )
        if "AAPL" not in str(outcome.output):
            s.fail("live_agent", f"output={outcome.output}")
            return False
        s.ok("live_agent", outcome.output.summary[:120])
        return True
    except Exception as exc:
        s.fail("live_agent", f"{exc} (set SKIP_TERMINAL_LIVE_AGENT=1 to skip)")
        return False


def print_summary(s: VerifyState) -> int:
    table = Table(title="Agent terminal verification")
    table.add_column("Check")
    table.add_column("Status")
    table.add_column("Detail")
    failed = 0
    for r in s.results:
        status = "[green]PASS[/green]" if r.passed else "[red]FAIL[/red]"
        if not r.passed:
            failed += 1
        table.add_row(r.name, status, r.detail[:120])
    console.print(table)
    return 1 if failed else 0


async def run_verify(base_url: str, session_id: str, *, skip_live: bool) -> int:
    global state
    state = VerifyState(base_url=base_url.rstrip("/"), session_id=session_id)
    if skip_live:
        os.environ["SKIP_TERMINAL_LIVE_AGENT"] = "1"

    if not phase0_preconditions(state):
        return print_summary(state)
    if not phase1_api_smoke(state):
        print_summary(state)
        return 1
    if not phase2_library_matrix(state):
        print_summary(state)
        return 1
    if not await phase3_python_client(state):
        print_summary(state)
        return 1
    if not phase4_limits(state):
        print_summary(state)
        return 1
    if not phase5_scenarios(state):
        print_summary(state)
        return 1
    phase1_cleanup(state)
    await phase6_live_agent(state)
    return print_summary(state)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-url",
        default=os.environ.get("TERMINAL_SERVICE_URL", "http://agent-terminal:8001"),
    )
    parser.add_argument(
        "--session-id",
        default=f"verify-{int(time.time())}",
    )
    parser.add_argument(
        "--skip-live-agent",
        action="store_true",
        help="Skip Phase 6 LLM smoke test",
    )
    args = parser.parse_args()
    code = asyncio.run(
        run_verify(args.base_url, args.session_id, skip_live=args.skip_live_agent)
    )
    sys.exit(code)


if __name__ == "__main__":
    main()
