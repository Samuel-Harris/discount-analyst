# Agent-terminal images and verification (requires Docker).
export DOCKER_BUILDKIT := 1

SANDBOX_IMAGE := discount-analyst-terminal-sandbox:local
SANDBOX_CONTEXT := backend/services/agent_terminal

.PHONY: build-terminal-sandbox build-terminal-sandbox-force \
	ensure-agent-terminal rebuild-agent-terminal verify-terminal

build-terminal-sandbox-force:
	docker build -f $(SANDBOX_CONTEXT)/Dockerfile.sandbox \
		-t $(SANDBOX_IMAGE) $(SANDBOX_CONTEXT)

build-terminal-sandbox:
	@if docker image inspect $(SANDBOX_IMAGE) >/dev/null 2>&1; then \
		echo "$(SANDBOX_IMAGE) already exists; skip build (make build-terminal-sandbox-force to rebuild)"; \
	else \
		$(MAKE) build-terminal-sandbox-force; \
	fi

ensure-agent-terminal:
	@if curl -sf http://127.0.0.1:8001/health >/dev/null; then \
		echo "agent-terminal already healthy"; \
	else \
		$(MAKE) build-terminal-sandbox && \
		TERMINAL_WORKSPACE_HOST_PATH="$${TERMINAL_WORKSPACE_HOST_PATH:-$$(pwd)}" \
		docker compose up -d --wait --wait-timeout 60 agent-terminal; \
	fi

rebuild-agent-terminal: build-terminal-sandbox-force
	TERMINAL_WORKSPACE_HOST_PATH="$${TERMINAL_WORKSPACE_HOST_PATH:-$$(pwd)}" \
	docker compose up -d --wait --wait-timeout 60 --build --force-recreate agent-terminal

# Publish orchestrator on :8001 via docker-compose.yml; optional repo bind for sandboxes.
verify-terminal: build-terminal-sandbox-force
	TERMINAL_WORKSPACE_HOST_PATH="$$(pwd)" \
	TERMINAL_SERVICE_URL=http://127.0.0.1:8001 \
	uv run python backend/tools/verify_agent_terminal.py --skip-live-agent
