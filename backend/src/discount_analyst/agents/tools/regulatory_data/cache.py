from __future__ import annotations

import json
import os
from collections.abc import Awaitable, Callable, Generator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from discount_analyst.agents.tools.regulatory_data.errors import ColdCacheError
from discount_analyst.agents.tools.regulatory_data.models import (
    CacheManifest,
    CacheSource,
    SourceSnapshot,
    utc_now,
)

LAZY_REFRESH_TTL = timedelta(hours=24)
_MANIFEST_NAME = "manifest.json"

TTL_SEC_TICKERS = "sec_company_tickers"
TTL_SEC_SUBMISSIONS = "sec_submissions"
TTL_SEC_COMPANYFACTS_LIVE = "sec_companyfacts_live"


class RegulatoryDataCache:
    """Versioned bulk snapshots plus an atomically replaced manifest.

    File-TTL overlays (SEC tickers, submissions, companyfacts gap-fill) live
    beside the versioned tree and are never recorded in the manifest. A failed
    publish leaves the previous complete snapshot in place.
    """

    def __init__(self, root: Path) -> None:
        self.root = root

    @classmethod
    def from_settings(cls) -> RegulatoryDataCache:
        from discount_analyst.config.settings import settings as app_settings

        return cls(app_settings.regulatory_data_cache_dir)

    @property
    def manifest_path(self) -> Path:
        return self.root / _MANIFEST_NAME

    def ttl_file(self, *parts: str) -> Path:
        return self.root.joinpath(*parts)

    def load_manifest(self) -> CacheManifest:
        if not self.manifest_path.is_file():
            return CacheManifest()
        return CacheManifest.model_validate_json(self.manifest_path.read_text())

    def snapshot_for(self, source: CacheSource | str) -> SourceSnapshot | None:
        return self.load_manifest().sources.get(_source_key(source))

    def active_dir(self, source: CacheSource | str) -> Path | None:
        snapshot = self.snapshot_for(source)
        if snapshot is None:
            return None
        path = self.root / snapshot.relative_path
        if not path.exists():
            return None
        return path

    def begin_version(self, source: CacheSource | str) -> tuple[str, Path]:
        version_id = utc_now().strftime("%Y%m%dT%H%M%SZ") + f"-{uuid4().hex[:8]}"
        path = self.root / _source_key(source) / version_id
        path.mkdir(parents=True, exist_ok=True)
        return version_id, path

    def publish(
        self,
        source: CacheSource | str,
        *,
        version_id: str,
        record_count: int,
        downloaded_version_or_date: str = "",
    ) -> SourceSnapshot:
        key = _source_key(source)
        relative_path = f"{key}/{version_id}"
        snapshot = SourceSnapshot(
            source=key,
            version_id=version_id,
            relative_path=relative_path,
            refreshed_at=utc_now(),
            record_count=record_count,
            downloaded_version_or_date=downloaded_version_or_date or version_id,
        )
        manifest = self.load_manifest()
        manifest.sources[key] = snapshot
        self.root.mkdir(parents=True, exist_ok=True)
        write_json_atomically(self.manifest_path, manifest.model_dump(mode="json"))
        return snapshot

    def discard_version(self, source: CacheSource | str, version_id: str) -> None:
        path = self.root / _source_key(source) / version_id
        if path.exists():
            _remove_tree(path)

    @contextmanager
    def publishing(
        self, source: CacheSource
    ) -> Generator[tuple[Path, Callable[..., SourceSnapshot]]]:
        version_id, version_dir = self.begin_version(source)
        snapshot: SourceSnapshot | None = None

        def publish(
            *, record_count: int, downloaded_version_or_date: str = ""
        ) -> SourceSnapshot:
            nonlocal snapshot
            snapshot = self.publish(
                source,
                version_id=version_id,
                record_count=record_count,
                downloaded_version_or_date=downloaded_version_or_date,
            )
            return snapshot

        try:
            yield version_dir, publish
        except BaseException:
            if snapshot is None:
                self.discard_version(source, version_id)
            raise
        if snapshot is None:
            self.discard_version(source, version_id)
            raise RuntimeError(f"{source} refresh did not publish a snapshot")

    def is_fresh(
        self,
        source: CacheSource | str,
        *,
        ttl: timedelta = LAZY_REFRESH_TTL,
    ) -> bool:
        snapshot = self.snapshot_for(source)
        if snapshot is None:
            return False
        age = utc_now() - snapshot.refreshed_at
        return age <= ttl

    def file_is_fresh(self, path: Path, *, ttl: timedelta = LAZY_REFRESH_TTL) -> bool:
        if not path.is_file():
            return False
        modified = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
        return utc_now() - modified <= ttl


async def ensure_fresh_snapshot(
    cache: RegulatoryDataCache,
    source: CacheSource,
    refresh: Callable[[], Awaitable[object]],
    *,
    refresh_flags: str,
) -> tuple[SourceSnapshot, Path]:
    if not cache.is_fresh(source):
        try:
            await refresh()
        except Exception as exc:
            if cache.active_dir(source) is None:
                raise ColdCacheError(str(source), refresh_flags=refresh_flags) from exc
    snapshot = cache.snapshot_for(source)
    active_dir = cache.active_dir(source)
    if snapshot is None or active_dir is None:
        raise ColdCacheError(str(source), refresh_flags=refresh_flags)
    return snapshot, active_dir


def write_bytes_atomically(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        tmp.write_bytes(data)
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def write_text_atomically(path: Path, text: str) -> None:
    write_bytes_atomically(path, text.encode())


def write_json_atomically(path: Path, payload: object) -> None:
    write_text_atomically(path, json.dumps(payload, indent=2, sort_keys=True))


def _source_key(source: CacheSource | str) -> str:
    return source.value if isinstance(source, CacheSource) else source


def _remove_tree(path: Path) -> None:
    if path.is_file() or path.is_symlink():
        path.unlink()
        return
    for child in path.iterdir():
        _remove_tree(child)
    path.rmdir()
