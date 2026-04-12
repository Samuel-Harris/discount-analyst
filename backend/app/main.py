"""FastAPI entrypoint for the local dashboard."""

from __future__ import annotations

from fastapi import FastAPI

from backend.db.migrate import migrate_to_head
from backend.db.session import create_dashboard_engine, create_session_factory
from backend.pipeline.sqlmodel_runner import DashboardPipelineRunner
from backend.routers import agents, portfolio, workflow_runs
from backend.settings.config import DashboardSettings


def create_app(settings: DashboardSettings | None = None) -> FastAPI:
    settings = settings or DashboardSettings()
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_dashboard_engine(settings)
    migrate_to_head(str(engine.url))
    session_factory = create_session_factory(engine)

    app = FastAPI(title="Discount Analyst Dashboard")
    app.state.db_engine = engine
    app.state.db_session_factory = session_factory
    app.state.settings = settings
    app.state.pipeline_runner = DashboardPipelineRunner(session_factory, settings)

    @app.on_event("shutdown")
    def _dispose_engine() -> None:
        app.state.db_engine.dispose()

    app.include_router(workflow_runs.router, prefix="/api")
    app.include_router(agents.router, prefix="/api")
    app.include_router(portfolio.router, prefix="/api")

    return app


app = create_app()
