"""Engine and session-factory helpers for dashboard persistence."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, create_engine

from backend.settings import DashboardSettings

SessionFactory = Callable[[], Session]


def sqlite_url_from_path(database_path: Path) -> str:
    return f"sqlite:///{database_path}"


def create_dashboard_engine(settings: DashboardSettings) -> Engine:
    return create_engine(
        sqlite_url_from_path(settings.database_path),
        connect_args={"check_same_thread": False},
    )


def create_session_factory(engine: Engine) -> SessionFactory:
    return sessionmaker(bind=engine, class_=Session, expire_on_commit=False)
