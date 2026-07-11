# Agent-terminal verification (requires Docker and built sandbox image).
.PHONY: build-terminal-sandbox verify-terminal

build-terminal-sandbox:
	docker build -f backend/services/agent_terminal/Dockerfile.sandbox \
		-t discount-analyst-terminal-sandbox:local .

# Publish orchestrator on :8001 via docker-compose.yml; optional repo bind for sandboxes.
verify-terminal: build-terminal-sandbox
	TERMINAL_WORKSPACE_HOST_PATH="$$(pwd)" \
	TERMINAL_SERVICE_URL=http://127.0.0.1:8001 \
	uv run python backend/tools/verify_agent_terminal.py --skip-live-agent
