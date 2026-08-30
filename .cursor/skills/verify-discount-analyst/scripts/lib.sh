# Shared helpers for verify-discount-analyst. Sourced by launch/doctor/seed/cleanup.

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ARTEFACTS_DIR="$REPO_ROOT/.cursor/artefacts/verify-discount-analyst"
RUN_DIR="$ARTEFACTS_DIR/run"
EVIDENCE_DIR="$ARTEFACTS_DIR/evidence"
STATE_FILE="$RUN_DIR/state.env"

DEFAULT_API_PORT="${VERIFY_API_PORT:-18080}"
DEFAULT_UI_PORT="${VERIFY_UI_PORT:-15173}"

die() {
  echo "verify-discount-analyst: $*" >&2
  exit 1
}

pid_alive() {
  local pid="$1"
  [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null
}

listener_pids() {
  local port="$1"
  lsof -nP -iTCP:"$port" -sTCP:LISTEN -t 2>/dev/null || true
}

port_in_use() {
  local port="$1"
  [[ -n "$(listener_pids "$port")" ]]
}

load_state() {
  [[ -f "$STATE_FILE" ]] || die "no run state at $STATE_FILE — launch first"
  # shellcheck disable=SC1090
  source "$STATE_FILE"
  [[ -n "${RUN_ID:-}" && -n "${API_PID:-}" && -n "${UI_PID:-}" ]] || die "state file is incomplete"
}

wait_http() {
  local url="$1"
  local needle="$2"
  local timeout_s="${3:-60}"
  local elapsed=0
  while (( elapsed < timeout_s )); do
    if curl -fsS --max-time 2 "$url" 2>/dev/null | grep -q "$needle"; then
      return 0
    fi
    sleep 1
    elapsed=$((elapsed + 1))
  done
  return 1
}
