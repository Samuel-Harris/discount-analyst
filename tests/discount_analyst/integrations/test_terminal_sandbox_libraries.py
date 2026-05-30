"""Docker integration: full sandbox scientific/financial library matrix."""

from __future__ import annotations

import base64
import os
import shutil

import httpx
import pytest

LIBRARY_MATRIX_SCRIPT = """
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
r, n, fcf = sp.symbols("r n fcf")
pv = fcf * (1 - (1 + r) ** (-n)) / r
ok &= check("sympy", lambda: str(sp.solve(pv - fcf, pv)[0])[:20] if False else str(pv)[:20])

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
    print(f"WARN pandas_datareader_fred: {exc}")

import yfinance as yf
hist = yf.Ticker("AAPL").history(period="5d")
if hist.empty or "Close" not in hist.columns:
    raise RuntimeError("yfinance returned empty history")
ok &= check("yfinance", lambda: f"closes={len(hist)}")

if not ok:
    sys.exit(1)
print("MATRIX_OK")
"""


def _matrix_command() -> str:
    encoded = base64.b64encode(LIBRARY_MATRIX_SCRIPT.encode()).decode()
    return (
        f'python -c "import base64; '
        f"exec(base64.b64decode('{encoded}').decode(), {{'__name__': '__main__'}})\""
    )


@pytest.mark.docker
@pytest.mark.anyio
async def test_sandbox_library_matrix() -> None:
    """Requires Docker, sandbox image, and orchestrator (TERMINAL_SERVICE_URL)."""
    if shutil.which("docker") is None:
        pytest.skip("docker CLI not available")

    base = os.environ.get("TERMINAL_SERVICE_URL", "http://127.0.0.1:8001").rstrip("/")
    session_id = "pytest-terminal-library-matrix"

    async with httpx.AsyncClient(timeout=300.0) as client:
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
            f"/sessions/{session_id}/exec",
            json={"command": _matrix_command()},
        )
        exec_resp.raise_for_status()
        payload = exec_resp.json()
        assert payload["exit_code"] == 0, payload.get("stderr", "")
        assert "MATRIX_OK" in payload["stdout"]

        await client.delete(f"/sessions/{session_id}")
