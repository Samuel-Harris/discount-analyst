"""FastAPI entrypoint for the local dashboard."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import logfire
from fastapi import FastAPI

from backend.db.migrate import migrate_to_head
from backend.db.session import create_dashboard_engine, create_session_factory
from backend.observability.logging import configure_dashboard_observability
from backend.pipeline.sqlmodel_runner import DashboardPipelineRunner
from backend.routers import agents, portfolio, workflow_runs
from backend.settings.config import DashboardSettings


def create_app(settings: DashboardSettings | None = None) -> FastAPI:
    settings = settings or DashboardSettings()
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
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
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


app = create_app()
