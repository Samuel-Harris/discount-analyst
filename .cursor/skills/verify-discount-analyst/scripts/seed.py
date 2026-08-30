"""Seed the verification SQLite with one completed mock workflow."""

from __future__ import annotations

from sqlmodel import Session

from discount_analyst.adapters.persistence.session import create_dashboard_engine
from discount_analyst.composition.dev_seed import seed
from discount_analyst.config.settings import load_settings


def main() -> None:
    settings = load_settings()
    engine = create_dashboard_engine(settings)
    with Session(engine) as session:
        seed(session)
    print(settings.database_path.resolve())


if __name__ == "__main__":
    main()
