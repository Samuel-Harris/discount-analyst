set default-list := true

# Serve the API on port 8000.
[working-directory(justfile_directory())]
backend:
    uv run uvicorn discount_analyst.composition.api:create_app --factory --reload --host 127.0.0.1 --port 8000

# Serve the dashboard on port 5173.
[working-directory(justfile_directory())]
frontend:
    pnpm --dir frontend run dev

# Serve the terminal, the API, and Vite. Interrupt stops all three.
[working-directory(justfile_directory())]
stack:
    #!/usr/bin/env bash
    set -euo pipefail
    # One shell has to own the children. A line-wise recipe starts a new shell
    # per line, so the trap that stops both servers and the terminal lives here.
    # Job control puts each background `just` in its own process group.
    set -m

    api_pid=""
    vite_pid=""

    stop_group() {
        local pid="$1"
        if [[ -z "${pid}" ]]; then
            return 0
        fi
        kill -TERM -- "-${pid}" 2>/dev/null || true
        wait "${pid}" 2>/dev/null || true
    }

    # An exec failure exits within this window. A later crash is caught by the loop below.
    stay_up() {
        local pid="$1"
        local i=0
        while [[ "${i}" -lt 5 ]]; do
            if ! kill -0 "${pid}" 2>/dev/null; then
                return 1
            fi
            sleep 0.1
            i=$((i + 1))
        done
        return 0
    }

    cleanup() {
        local status="$1"
        local compose_status=0
        trap '' INT TERM
        trap - EXIT
        stop_group "${api_pid}"
        stop_group "${vite_pid}"
        # `just run terminal ensure` returns success when port 8001 is already
        # healthy. This recipe still owns that container, so every exit tears it down.
        docker compose down || compose_status=$?
        if [[ "${status}" -eq 0 ]]; then
            status="${compose_status}"
        fi
        exit "${status}"
    }

    trap 'cleanup $?' EXIT
    trap 'cleanup 130' INT
    trap 'cleanup 143' TERM

    # The ensure recipe owns the make line. It returns before either server starts.
    "{{just_executable()}}" run terminal ensure

    # The settings default is the Compose DNS name, which the host cannot resolve.
    if [[ -z "${TERMINAL_SERVICE_URL:-}" ]]; then
        export TERMINAL_SERVICE_URL=http://127.0.0.1:8001
    fi

    # The backend and frontend recipes own the server command lines.
    "{{just_executable()}}" run backend &
    api_pid=$!
    if ! stay_up "${api_pid}"; then
        wait "${api_pid}" || cleanup $?
        cleanup 0
    fi

    "{{just_executable()}}" run frontend &
    vite_pid=$!
    if ! stay_up "${vite_pid}"; then
        wait "${vite_pid}" || cleanup $?
        cleanup 0
    fi

    # `/bin/bash` on macOS is 3.2 and has no `wait -n`.
    while true; do
        if ! kill -0 "${api_pid}" 2>/dev/null; then
            wait "${api_pid}" || cleanup $?
            cleanup 0
        fi
        if ! kill -0 "${vite_pid}" 2>/dev/null; then
            wait "${vite_pid}" || cleanup $?
            cleanup 0
        fi
        sleep 0.5
    done

# Build, start, and stop the agent terminal.
mod terminal 'terminal.just'
