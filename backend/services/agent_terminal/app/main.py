"""FastAPI orchestrator: create per-session sandbox containers and run docker exec."""

from __future__ import annotations

import asyncio
import logging
import os
import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Annotated, Any, cast

import docker
import docker.errors
from docker import DockerClient
from docker.models.containers import Container
from fastapi import FastAPI, HTTPException, Path
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

SANDBOX_IMAGE = os.environ.get(
    "TERMINAL_SANDBOX_IMAGE", "discount-analyst-terminal-sandbox:local"
)
DOCKER_RUNTIME = os.environ.get("DOCKER_RUNTIME", "runc")
SESSION_LABEL_KEY = "discount-analyst.terminal.session"
CONTAINER_PREFIX = "da-term-"
MEM_LIMIT = os.environ.get("TERMINAL_CONTAINER_MEM", "4g")
NANO_CPUS = int(os.environ.get("TERMINAL_CONTAINER_NANO_CPUS", str(2 * 10**9)))
COMMAND_TIMEOUT_S = int(os.environ.get("TERMINAL_COMMAND_TIMEOUT_S", "300"))
MAX_OUTPUT_BYTES = int(
    os.environ.get("TERMINAL_MAX_OUTPUT_BYTES", str(2 * 1024 * 1024))
)
SESSION_SWEEP_INTERVAL_S = int(
    os.environ.get("TERMINAL_SESSION_SWEEP_INTERVAL_S", "600")
)
SESSION_MAX_AGE_S = int(os.environ.get("TERMINAL_SESSION_MAX_AGE_S", "7200"))
WORKSPACE_HOST_PATH = os.environ.get("TERMINAL_WORKSPACE_HOST_PATH", "").strip()
WORKSPACE_CONTAINER_PATH = os.environ.get(
    "TERMINAL_WORKSPACE_CONTAINER_PATH", "/workspace/repo"
).strip()


def _container_name(session_id: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in session_id)
    return f"{CONTAINER_PREFIX}{safe}"[:128]


def _docker_client() -> DockerClient:
    return docker.from_env()


def _truncate_streams(
    stdout: bytes, stderr: bytes, max_bytes: int
) -> tuple[bytes, bytes, bool]:
    total = len(stdout) + len(stderr)
    if total <= max_bytes:
        return stdout, stderr, False
    if len(stdout) >= max_bytes:
        return stdout[:max_bytes], b"", True
    rest = max_bytes - len(stdout)
    return stdout, stderr[:rest], True


def _parse_exec_result(
    exit_code: int | None,
    output: tuple[bytes | None, bytes | None] | bytes | None,
) -> tuple[int, bytes, bytes]:
    code = int(exit_code) if exit_code is not None else -1
    if output is None:
        return code, b"", b""
    if isinstance(output, bytes):
        return code, output, b""
    stdout_b, stderr_b = output
    return code, stdout_b or b"", stderr_b or b""


class SessionCreate(BaseModel):
    session_id: str = Field(min_length=1, max_length=128)


class ExecRequest(BaseModel):
    command: str = Field(min_length=1)


class ExecResponse(BaseModel):
    exit_code: int
    stdout: str
    stderr: str
    truncated: bool


class SessionState(BaseModel):
    session_id: str
    container_id: str
    container_name: str


def _container_labels(container: Container) -> dict[str, str]:
    """Read session labels from container attrs (stubs omit ``Container.labels`` typing)."""
    raw_config = container.attrs.get("Config")
    if not isinstance(raw_config, dict):
        return {}
    config = cast(dict[str, Any], raw_config)
    labels_value = config.get("Labels")
    if not isinstance(labels_value, dict):
        return {}
    return cast(dict[str, str], labels_value)


def _require_container_id(container: Container) -> str:
    container_id = container.id
    if not container_id:
        raise HTTPException(status_code=500, detail="Container has no Docker id")
    return container_id


def _container_display_name(container: Container) -> str:
    return (container.name or "").lstrip("/")


def _session_state_from_container(
    session_id: str, container: Container
) -> SessionState:
    return SessionState(
        session_id=session_id,
        container_id=_require_container_id(container),
        container_name=_container_display_name(container),
    )


_sessions: dict[str, Container] = {}
_client: DockerClient | None = None
_sweep_task: asyncio.Task[None] | None = None


def _get_client() -> DockerClient:
    global _client  # noqa: PLW0603
    if _client is None:
        _client = _docker_client()
    return _client


async def _sweep_old_sessions() -> None:
    """Remove labelled sandbox containers older than SESSION_MAX_AGE_S (best-effort)."""
    while True:
        await asyncio.sleep(SESSION_SWEEP_INTERVAL_S)
        try:
            client = _get_client()
            now = time.time()
            for container in client.containers.list(
                all=True,
                filters={"label": SESSION_LABEL_KEY},
            ):
                label_sid = _container_labels(container).get(SESSION_LABEL_KEY)
                if label_sid is None:
                    continue
                started_at = container.attrs.get("State", {}).get("StartedAt", "")
                try:
                    if (
                        isinstance(started_at, str)
                        and started_at
                        and started_at != "0001-01-01T00:00:00Z"
                    ):
                        dt = datetime.fromisoformat(
                            started_at.replace("Z", "+00:00")
                        ).astimezone(UTC)
                        age = now - dt.timestamp()
                    else:
                        age = 0.0
                except (OSError, TypeError, ValueError):
                    age = 0.0
                if age < SESSION_MAX_AGE_S:
                    continue
                try:
                    container.stop(timeout=10)
                    container.remove(v=True, force=True)
                    logger.info(
                        "Swept old terminal session container %s", container.short_id
                    )
                except docker.errors.APIError as exc:
                    logger.warning("Sweep failed for %s: %s", container.short_id, exc)
                _sessions.pop(label_sid, None)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Terminal session sweep iteration failed")


@asynccontextmanager
async def _lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    global _sweep_task, _client  # noqa: PLW0603
    sweep_task = asyncio.create_task(_sweep_old_sessions())
    _sweep_task = sweep_task
    try:
        yield
    finally:
        sweep_task.cancel()
        try:
            await sweep_task
        except asyncio.CancelledError:
            pass
        _sweep_task = None
        if _client is not None:
            _client.close()
            _client = None


app = FastAPI(
    title="Discount Analyst agent-terminal",
    version="1.0.0",
    lifespan=_lifespan,
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


def _run_sandbox_container(
    client: DockerClient, *, session_id: str, name: str
) -> Container:
    run_kwargs: dict[str, Any] = {
        "image": SANDBOX_IMAGE,
        "name": name,
        "command": ["sleep", "infinity"],
        "detach": True,
        "network_mode": "bridge",
        "mem_limit": MEM_LIMIT,
        "nano_cpus": NANO_CPUS,
        "labels": {SESSION_LABEL_KEY: session_id},
        "remove": False,
        "stdin_open": False,
        "tty": False,
    }
    if DOCKER_RUNTIME:
        run_kwargs["runtime"] = DOCKER_RUNTIME
    if WORKSPACE_HOST_PATH:
        run_kwargs["volumes"] = [f"{WORKSPACE_HOST_PATH}:{WORKSPACE_CONTAINER_PATH}:ro"]
    return cast(Container, client.containers.run(**run_kwargs))


@app.post("/sessions", response_model=SessionState)
async def create_session(body: SessionCreate) -> SessionState:
    """Create (or reuse) a sandbox container for ``session_id``."""
    sid = body.session_id
    existing = _sessions.get(sid)
    if existing is not None:
        try:
            existing.reload()
            if existing.status == "running":
                return _session_state_from_container(sid, existing)
        except docker.errors.NotFound:
            _sessions.pop(sid, None)

    client = _get_client()
    name = _container_name(sid)
    try:
        by_name = client.containers.get(name)
        by_name.reload()
        if by_name.status == "running":
            _sessions[sid] = by_name
            return _session_state_from_container(sid, by_name)
        by_name.remove(force=True)
    except docker.errors.NotFound:
        pass

    try:
        container = _run_sandbox_container(client, session_id=sid, name=name)
    except docker.errors.APIError as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Failed to start sandbox container (runtime={DOCKER_RUNTIME!r}): {exc}. "
                "If runsc is unavailable, set DOCKER_RUNTIME=runc for development."
            ),
        ) from exc

    _sessions[sid] = container
    return _session_state_from_container(sid, container)


def _exec_blocking(container_id: str, command: str) -> tuple[int, bytes, bytes]:
    client = _get_client()
    container = client.containers.get(container_id)
    exit_code, output = container.exec_run(
        cmd=["/bin/sh", "-c", command],
        demux=True,
    )
    demuxed = cast(tuple[bytes | None, bytes | None] | bytes | None, output)
    return _parse_exec_result(exit_code, demuxed)


@app.post("/sessions/{session_id}/exec", response_model=ExecResponse)
async def exec_command(
    session_id: Annotated[str, Path(min_length=1, max_length=128)],
    body: ExecRequest,
) -> ExecResponse:
    container = _sessions.get(session_id)
    if container is None:
        client = _get_client()
        name = _container_name(session_id)
        try:
            by_name = client.containers.get(name)
            by_name.reload()
            if by_name.status != "running":
                raise HTTPException(
                    status_code=404,
                    detail="Unknown session_id or container not running",
                )
            _sessions[session_id] = by_name
            container = by_name
        except docker.errors.NotFound as exc:
            raise HTTPException(status_code=404, detail="Unknown session_id") from exc
    try:
        container.reload()
    except docker.errors.NotFound as exc:
        _sessions.pop(session_id, None)
        raise HTTPException(
            status_code=404, detail="Container no longer exists"
        ) from exc

    container_id = _require_container_id(container)
    try:
        exit_code, stdout_b, stderr_b = await asyncio.wait_for(
            asyncio.to_thread(_exec_blocking, container_id, body.command),
            timeout=COMMAND_TIMEOUT_S,
        )
    except TimeoutError as exc:
        raise HTTPException(
            status_code=504,
            detail=f"Command exceeded timeout ({COMMAND_TIMEOUT_S}s)",
        ) from exc

    stdout_b, stderr_b, truncated = _truncate_streams(
        stdout_b, stderr_b, MAX_OUTPUT_BYTES
    )
    return ExecResponse(
        exit_code=exit_code,
        stdout=stdout_b.decode("utf-8", errors="replace"),
        stderr=stderr_b.decode("utf-8", errors="replace"),
        truncated=truncated,
    )


@app.delete("/sessions/{session_id}", status_code=204)
async def delete_session(
    session_id: Annotated[str, Path(min_length=1, max_length=128)],
) -> None:
    container = _sessions.pop(session_id, None)
    if container is None:
        try:
            client = _get_client()
            name = _container_name(session_id)
            c = client.containers.get(name)
            c.stop(timeout=10)
            c.remove(v=True, force=True)
        except docker.errors.NotFound:
            return
        except docker.errors.APIError as exc:
            logger.warning("delete_session: %s", exc)
        return

    try:
        container.stop(timeout=10)
        container.remove(v=True, force=True)
    except docker.errors.NotFound:
        return
    except docker.errors.APIError as exc:
        logger.warning("delete_session: %s", exc)
