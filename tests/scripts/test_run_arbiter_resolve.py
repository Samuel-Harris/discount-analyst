"""Resolver behaviour for ``scripts/agents/run_arbiter.py``."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from scripts.agents.run_arbiter import Selector, resolve_targets


def test_resolve_targets_requires_dcf_result(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_appr = MagicMock()
    fake_appr.ticker = "TST"
    fake_appr.dcf_result = None

    def fake_load_appraiser(_path: Path) -> MagicMock:
        return fake_appr

    monkeypatch.setattr(
        "scripts.agents.run_arbiter._load_appraiser_run_output",
        fake_load_appraiser,
    )

    sel = Selector(Path("/tmp/does-not-need-to-exist.json"), None, "raw")
    with pytest.raises(ValueError, match="dcf_result"):
        resolve_targets([sel], is_existing_position=False)
