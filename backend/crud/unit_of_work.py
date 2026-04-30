"""Session transaction boundaries for dashboard persistence.

CRUD helpers in ``backend.crud`` generally mutate the current ``Session`` only.
Callers that own the unit of work (pipeline runner thread, FastAPI handlers,
tests) must ``commit`` (or use ``Session.begin``) at an explicit boundary.
"""

from __future__ import annotations

from sqlmodel import Session


def commit_transaction(session: Session) -> None:
    """Flush and commit all pending ORM state for this session."""
    session.commit()
