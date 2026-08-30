import pytest

from discount_analyst.agents.tools.regulatory_data.models import SourceRefreshResult
from discount_analyst.agents.tools.regulatory_data.refresh import (
    refresh_jobs,
    refresh_selected,
    resolve_refresh_flags,
)
from discount_analyst.composition.cli import main
from discount_analyst.entrypoints.cli.main import main as entrypoint_main


def test_console_script_exports_main() -> None:
    assert main is entrypoint_main


def test_refresh_script_help_exits_zero(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as caught:
        main(["admin", "refresh-regulatory-data", "--help"])
    assert caught.value.code == 0
    output = capsys.readouterr().out
    assert "--exchanges" in output
    assert "--sec" in output
    assert "--companies-house" in output


def test_unknown_admin_command_exits() -> None:
    with pytest.raises(SystemExit, match="Unknown admin command"):
        main(["admin", "not-a-real-admin"])


def test_no_source_flags_selects_all() -> None:
    assert resolve_refresh_flags(exchanges=False, sec=False, companies_house=False) == (
        True,
        True,
        True,
    )


def test_source_flags_are_respected() -> None:
    names = [
        name
        for name, _job in refresh_jobs(exchanges=True, sec=False, companies_house=False)
    ]
    assert names == ["nasdaq_trader", "lse_issuers"]
    names = [
        name
        for name, _job in refresh_jobs(exchanges=False, sec=True, companies_house=False)
    ]
    assert names == ["sec_edgar"]
    names = [
        name
        for name, _job in refresh_jobs(exchanges=False, sec=False, companies_house=True)
    ]
    assert names == ["companies_house"]


async def test_refresh_selected_collects_success_and_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def ok() -> SourceRefreshResult:
        return SourceRefreshResult(
            source="nasdaq_trader",
            version_id="v1",
            downloaded_version_or_date="today",
            record_count=2,
            cache_path="/tmp/cache",
            skipped_or_idempotent_count=0,
            active_snapshot="nasdaq_trader/v1",
        )

    async def boom() -> SourceRefreshResult:
        raise RuntimeError("schema changed")

    monkeypatch.setattr(
        "discount_analyst.agents.tools.regulatory_data.refresh.refresh_nasdaq_trader",
        ok,
    )
    monkeypatch.setattr(
        "discount_analyst.agents.tools.regulatory_data.refresh.refresh_lse_issuers",
        boom,
    )
    results, failures = await refresh_selected(
        exchanges=True, sec=False, companies_house=False
    )
    assert [item.source for item in results] == ["nasdaq_trader"]
    assert failures[0][0] == "lse_issuers"
    assert "schema changed" in str(failures[0][1])
