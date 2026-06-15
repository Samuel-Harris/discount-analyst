# Agent terminal (Docker orchestrator)

The **agent-terminal** service gives pipeline agents a per-run Linux sandbox via a single pydantic-ai tool, `terminal_exec(command)`. State (files under `/tmp`, cwd) persists for the duration of one agent run; the container is removed when the run finishes.

## Architecture

- **Orchestrator** (`Dockerfile.service`, FastAPI on port 8001): holds the Docker socket, creates sandbox containers, runs `docker exec`.
- **Sandbox** (`Dockerfile.sandbox`): Python 3.14 image with pandas, numpy, scipy, yfinance, sympy, statsmodels, matplotlib, and related libraries (see `requirements-sandbox.txt`).

The **backend** and CLI talk to the orchestrator over HTTP (`TERMINAL_SERVICE_URL`). Only the orchestrator mounts `/var/run/docker.sock`.

## Host prerequisites

1. **Docker** with API access from the orchestrator container.
2. **gVisor** (optional, production): install [runsc](https://gvisor.dev/docs/user_guide/install/) and set `DOCKER_RUNTIME=runsc`. Compose defaults to `runc` for local Docker Desktop.
3. **Sandbox image** (build once per machine or CI):

```bash
docker build -f docker/agent-terminal/Dockerfile.sandbox \
  -t discount-analyst-terminal-sandbox:local .
```

4. **Compose stack** (from repo root):

```bash
docker compose up --build
```

The orchestrator is published on **host port 8001** when using root `docker-compose.yml`.

### Optional: read-only project tree in sandboxes

Set `TERMINAL_WORKSPACE_HOST_PATH` to the **absolute host path** of the repo before `docker compose up` (paths are resolved by the Docker daemon, not inside the orchestrator container):

```bash
export TERMINAL_WORKSPACE_HOST_PATH="$(pwd)"
docker compose up --build
```

Sandboxes mount it at `/workspace/repo` (override with `TERMINAL_WORKSPACE_CONTAINER_PATH`).

### Verify stack

```bash
make verify-terminal   # builds sandbox image, runs scripts/verify_agent_terminal.py
```

Agent runs with terminal enabled probe session creation at startup (`ensure_terminal_ready` in `run_streamed_agent`). If the sandbox image is missing or Docker is misconfigured, the run fails immediately with `TerminalUnavailableError` including the orchestrator error detail — use `make verify-terminal` to diagnose locally.

Or from a running Compose backend:

```bash
docker compose exec -T backend uv run python scripts/verify_agent_terminal.py --skip-live-agent
```

## API

| Method   | Path                  | Description                                |
| -------- | --------------------- | ------------------------------------------ |
| `GET`    | `/health`             | Liveness                                   |
| `POST`   | `/sessions`           | Create or reuse sandbox for `session_id`   |
| `POST`   | `/sessions/{id}/exec` | Run shell command (`command` in JSON body) |
| `DELETE` | `/sessions/{id}`      | Stop and remove sandbox                    |

Limits (env on orchestrator): `TERMINAL_COMMAND_TIMEOUT_S` (default 300), `TERMINAL_MAX_OUTPUT_BYTES` (default 2MB), container `4g` RAM / 2 CPUs.

## Application settings

| Variable                            | Default                      | Purpose                                         |
| ----------------------------------- | ---------------------------- | ----------------------------------------------- |
| `DASHBOARD_USE_TERMINAL`            | `true`                       | Enable `terminal_exec` on agents                |
| `TERMINAL_SERVICE_URL`              | `http://agent-terminal:8001` | Orchestrator base URL                           |
| `TERMINAL_COMMAND_TIMEOUT_S`        | `300`                        | Per-command timeout (client read budget)        |
| `TERMINAL_MAX_OUTPUT_BYTES`         | `2097152`                    | Combined stdout+stderr cap                      |
| `TERMINAL_WORKSPACE_HOST_PATH`      | (empty)                      | Host path bind-mounted read-only into sandboxes |
| `TERMINAL_WORKSPACE_CONTAINER_PATH` | `/workspace/repo`            | Mount point inside sandboxes                    |
| `DOCKER_RUNTIME`                    | `runc` (orchestrator env)    | Container runtime (`runsc` for gVisor)          |

CLI/scripts: pass `--no-terminal` to disable for a single run.

## Local development without Compose

- Run the orchestrator locally (after building the sandbox image) and set `TERMINAL_SERVICE_URL=http://127.0.0.1:8001` (Compose publishes port 8001 by default), or
- Use `--no-terminal` / `DASHBOARD_USE_TERMINAL=false` when the orchestrator is not running.

## Data lifecycle

- No named volumes for sandboxes; each session uses the container writable layer only.
- Agent “memory” across commands in one run is the container filesystem; long-term artefacts are only what the model keeps in conversation stdout/stderr.
- Orphan containers are swept by label `discount-analyst.terminal.session` after `TERMINAL_SESSION_MAX_AGE_S` (default 2 hours).

## pandas-datareader note

`pandas-datareader` is installed for supplementary series; several sources are degraded or unmaintained. Agents should prefer **yfinance** for market data unless a specific datareader source is required.
