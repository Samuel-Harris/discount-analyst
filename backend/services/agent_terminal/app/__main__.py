"""Local process entry for the agent-terminal orchestrator."""

from __future__ import annotations

import uvicorn


def main() -> None:
    uvicorn.run("app.main:app", host="0.0.0.0", port=8001)


if __name__ == "__main__":
    main()
