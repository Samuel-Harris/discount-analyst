"""Wire the FastAPI dashboard application."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import logfire
import uvicorn
from fastapi import FastAPI

from discount_analyst.adapters.observability.logging import (
    configure_dashboard_observability,
)
from discount_analyst.adapters.orchestration.sqlmodel_runner import (
    DashboardPipelineRunner,
)
from discount_analyst.adapters.persistence.migrate import migrate_to_head
from discount_analyst.adapters.persistence.session import (
    create_dashboard_engine,
    create_session_factory,
)
from discount_analyst.config.settings import Settings, load_settings
from discount_analyst.entrypoints.api.routers import agents, portfolio, workflow_runs


def create_app(settings: Settings | None = None) -> FastAPI:
    """Composition root for the dashboard HTTP API."""
    settings = settings or load_settings()
    configure_dashboard_observability(settings)
    logfire.info(
        "Creating dashboard application",
        database_basename=settings.database_path.name,
    )
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_dashboard_engine(settings)
    migrate_to_head(str(engine.url))
    logfire.info(
        "Database migrations complete for dashboard",
        database_basename=settings.database_path.name,
    )
    session_factory = create_session_factory(engine)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
        logfire.info(
            "Dashboard API lifespan startup",
            database_basename=settings.database_path.name,
        )
        yield
        logfire.info("Dashboard API lifespan shutdown, disposing database engine")
        app.state.db_engine.dispose()

    app = FastAPI(title="Discount Analyst Dashboard", lifespan=lifespan)
    app.state.db_engine = engine
    app.state.db_session_factory = session_factory
    app.state.settings = settings
    app.state.pipeline_runner = DashboardPipelineRunner(session_factory, settings)

    app.include_router(workflow_runs.router, prefix="/api/workflow_runs")
    app.include_router(agents.router, prefix="/api/agents")
    app.include_router(portfolio.router, prefix="/api/portfolio")

    configure_dashboard_observability(settings, app)
    return app


if __name__ == "__main__":
    uvicorn.run(create_app(), host="127.0.0.1", port=8000)
