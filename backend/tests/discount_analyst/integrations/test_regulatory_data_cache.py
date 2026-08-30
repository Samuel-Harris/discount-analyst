from datetime import timedelta
from pathlib import Path

import pytest

from discount_analyst.agents.tools.regulatory_data.cache import (
    RegulatoryDataCache,
    write_text_atomically,
)
from discount_analyst.agents.tools.regulatory_data.models import CacheSource


def test_publish_replaces_manifest_atomically(tmp_path: Path) -> None:
    cache = RegulatoryDataCache(tmp_path)
    version_id, version_dir = cache.begin_version(CacheSource.NASDAQ_TRADER)
    (version_dir / "nasdaqlisted.txt").write_text("ok\n")
    snapshot = cache.publish(
        CacheSource.NASDAQ_TRADER,
        version_id=version_id,
        record_count=12,
        downloaded_version_or_date="2026-08-30",
    )
    assert cache.manifest_path.is_file()
    assert cache.active_dir(CacheSource.NASDAQ_TRADER) == version_dir
    assert snapshot.record_count == 12
    loaded = cache.load_manifest().sources["nasdaq_trader"]
    assert loaded.version_id == version_id
    assert loaded.downloaded_version_or_date == "2026-08-30"


def test_failed_publish_leaves_previous_snapshot(tmp_path: Path) -> None:
    cache = RegulatoryDataCache(tmp_path)
    first_id, first_dir = cache.begin_version(CacheSource.LSE_ISSUERS)
    (first_dir / "issuers.csv").write_text("ok\n")
    cache.publish(CacheSource.LSE_ISSUERS, version_id=first_id, record_count=5)

    second_id, second_dir = cache.begin_version(CacheSource.LSE_ISSUERS)
    (second_dir / "issuers.csv").write_text("partial\n")
    cache.discard_version(CacheSource.LSE_ISSUERS, second_id)

    assert cache.active_dir(CacheSource.LSE_ISSUERS) == first_dir
    assert cache.load_manifest().sources["lse_issuers"].version_id == first_id
    assert not second_dir.exists()


def test_missing_manifest_is_empty(tmp_path: Path) -> None:
    cache = RegulatoryDataCache(tmp_path / "absent")
    assert cache.load_manifest().sources == {}
    assert cache.active_dir(CacheSource.SEC_COMPANYFACTS) is None
    assert cache.is_fresh(CacheSource.SEC_COMPANYFACTS) is False


def test_file_ttl_helper(tmp_path: Path) -> None:
    cache = RegulatoryDataCache(tmp_path)
    path = tmp_path / "tickers.json"
    write_text_atomically(path, "{}")
    assert cache.file_is_fresh(path, ttl=timedelta(hours=24))
    assert cache.file_is_fresh(tmp_path / "missing.json") is False


def test_publishing_discards_on_failure(tmp_path: Path) -> None:
    cache = RegulatoryDataCache(tmp_path)
    first_id, first_dir = cache.begin_version(CacheSource.NASDAQ_TRADER)
    (first_dir / "ok.txt").write_text("ok\n")
    cache.publish(CacheSource.NASDAQ_TRADER, version_id=first_id, record_count=1)

    with pytest.raises(RuntimeError, match="ingest failed"):
        with cache.publishing(CacheSource.NASDAQ_TRADER) as (version_dir, _publish):
            (version_dir / "partial.txt").write_text("nope\n")
            raise RuntimeError("ingest failed")

    assert cache.active_dir(CacheSource.NASDAQ_TRADER) == first_dir
    assert cache.load_manifest().sources["nasdaq_trader"].version_id == first_id
