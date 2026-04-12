"""FastAPI dependencies shared across routers."""

from __future__ import annotations

from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, Request
from sqlmodel import Session


def get_session(request: Request) -> Generator[Session]:
    session_factory = request.app.state.db_session_factory
    with session_factory() as session:
        yield session


DbSession = Annotated[Session, Depends(get_session)]
