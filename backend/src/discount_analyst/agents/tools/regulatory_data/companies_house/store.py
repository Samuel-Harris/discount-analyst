import sqlite3
from datetime import date
from decimal import Decimal
from pathlib import Path

from discount_analyst.agents.tools.regulatory_data.cache import RegulatoryDataCache
from discount_analyst.agents.tools.regulatory_data.errors import (
    ColdCacheError,
    SchemaValidationError,
)
from discount_analyst.agents.tools.regulatory_data.models import CacheSource

SQLITE_FILENAME = "companies_house.sqlite"

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS companies (
    company_number TEXT PRIMARY KEY,
    company_name TEXT NOT NULL,
    company_status TEXT,
    company_type TEXT,
    name_normalised TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS companies_name_normalised
    ON companies (name_normalised);

CREATE TABLE IF NOT EXISTS accounts (
    source_document_id TEXT PRIMARY KEY,
    company_number TEXT NOT NULL,
    filed_at TEXT NOT NULL,
    period_end TEXT NOT NULL,
    currency TEXT,
    issuer_name TEXT,
    revenue TEXT,
    net_income TEXT,
    total_assets TEXT,
    total_liabilities TEXT,
    equity TEXT,
    cash TEXT,
    debt TEXT,
    shares_outstanding TEXT,
    accounts_filleted INTEGER NOT NULL,
    profit_and_loss_available INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS accounts_company_filed_period
    ON accounts (company_number, filed_at, period_end);
"""

_COMPANY_COLUMNS = frozenset(
    {
        "company_number",
        "company_name",
        "company_status",
        "company_type",
        "name_normalised",
    }
)
_ACCOUNT_COLUMNS = frozenset(
    {
        "source_document_id",
        "company_number",
        "filed_at",
        "period_end",
        "currency",
        "issuer_name",
        "revenue",
        "net_income",
        "total_assets",
        "total_liabilities",
        "equity",
        "cash",
        "debt",
        "shares_outstanding",
        "accounts_filleted",
        "profit_and_loss_available",
    }
)


def database_path(version_dir: Path) -> Path:
    return version_dir / SQLITE_FILENAME


def connect(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def initialise_database(version_dir: Path) -> sqlite3.Connection:
    version_dir.mkdir(parents=True, exist_ok=True)
    path = database_path(version_dir)
    connection = connect(path)
    connection.executescript(_SCHEMA_SQL)
    connection.commit()
    return connection


def require_active_database(cache: RegulatoryDataCache) -> Path:
    active = cache.active_dir(CacheSource.COMPANIES_HOUSE)
    if active is None:
        raise ColdCacheError("Companies House", refresh_flags="--companies-house")
    path = database_path(active)
    if not path.is_file():
        raise ColdCacheError("Companies House", refresh_flags="--companies-house")
    return path


def validate_database(connection: sqlite3.Connection) -> None:
    company_columns = _table_columns(connection, "companies")
    missing_companies = _COMPANY_COLUMNS - company_columns
    if missing_companies:
        raise SchemaValidationError(
            "Companies House",
            f"companies table missing columns {sorted(missing_companies)}",
        )
    account_columns = _table_columns(connection, "accounts")
    missing_accounts = _ACCOUNT_COLUMNS - account_columns
    if missing_accounts:
        raise SchemaValidationError(
            "Companies House",
            f"accounts table missing columns {sorted(missing_accounts)}",
        )
    company_count = connection.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
    if company_count < 1:
        raise SchemaValidationError("Companies House", "companies table is empty")


def fetch_company_by_number(
    connection: sqlite3.Connection, company_number: str
) -> sqlite3.Row | None:
    return connection.execute(
        "SELECT company_number, company_name, company_status, company_type "
        "FROM companies WHERE company_number = ?",
        (company_number,),
    ).fetchone()


def fetch_companies_by_normalised_name(
    connection: sqlite3.Connection, name_normalised: str
) -> list[sqlite3.Row]:
    return list(
        connection.execute(
            "SELECT company_number, company_name, company_status, company_type "
            "FROM companies WHERE name_normalised = ? "
            "ORDER BY company_number",
            (name_normalised,),
        )
    )


def fetch_account_as_of(
    connection: sqlite3.Connection,
    company_number: str,
    as_of: date | None,
) -> sqlite3.Row | None:
    if as_of is None:
        return connection.execute(
            "SELECT * FROM accounts WHERE company_number = ? "
            "ORDER BY filed_at DESC, period_end DESC LIMIT 1",
            (company_number,),
        ).fetchone()
    return connection.execute(
        "SELECT * FROM accounts WHERE company_number = ? AND filed_at <= ? "
        "ORDER BY filed_at DESC, period_end DESC LIMIT 1",
        (company_number, as_of.isoformat()),
    ).fetchone()


def upsert_company(
    connection: sqlite3.Connection,
    *,
    company_number: str,
    company_name: str,
    company_status: str | None,
    company_type: str | None,
    name_normalised: str,
) -> None:
    connection.execute(
        """
        INSERT INTO companies (
            company_number, company_name, company_status, company_type, name_normalised
        ) VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(company_number) DO UPDATE SET
            company_name = excluded.company_name,
            company_status = excluded.company_status,
            company_type = excluded.company_type,
            name_normalised = excluded.name_normalised
        """,
        (company_number, company_name, company_status, company_type, name_normalised),
    )


def insert_account(
    connection: sqlite3.Connection,
    *,
    source_document_id: str,
    company_number: str,
    filed_at: date,
    period_end: date,
    currency: str | None,
    issuer_name: str | None,
    revenue: Decimal | None,
    net_income: Decimal | None,
    total_assets: Decimal | None,
    total_liabilities: Decimal | None,
    equity: Decimal | None,
    cash: Decimal | None,
    debt: Decimal | None,
    shares_outstanding: Decimal | None,
    accounts_filleted: bool,
    profit_and_loss_available: bool,
) -> bool:
    cursor = connection.execute(
        """
        INSERT OR IGNORE INTO accounts (
            source_document_id, company_number, filed_at, period_end, currency,
            issuer_name, revenue, net_income, total_assets, total_liabilities,
            equity, cash, debt, shares_outstanding, accounts_filleted,
            profit_and_loss_available
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            source_document_id,
            company_number,
            filed_at.isoformat(),
            period_end.isoformat(),
            currency,
            issuer_name,
            decimal_to_text(revenue),
            decimal_to_text(net_income),
            decimal_to_text(total_assets),
            decimal_to_text(total_liabilities),
            decimal_to_text(equity),
            decimal_to_text(cash),
            decimal_to_text(debt),
            decimal_to_text(shares_outstanding),
            int(accounts_filleted),
            int(profit_and_loss_available),
        ),
    )
    return cursor.rowcount == 1


def account_count(connection: sqlite3.Connection) -> int:
    return int(connection.execute("SELECT COUNT(*) FROM accounts").fetchone()[0])


def company_count(connection: sqlite3.Connection) -> int:
    return int(connection.execute("SELECT COUNT(*) FROM companies").fetchone()[0])


def decimal_to_text(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return format(value, "f")


def decimal_from_text(value: str | None) -> Decimal | None:
    if value is None:
        return None
    return Decimal(value)


def _table_columns(connection: sqlite3.Connection, table: str) -> set[str]:
    if table not in {"companies", "accounts"}:
        raise ValueError(f"unknown table {table!r}")
    rows = connection.execute(f"PRAGMA table_info({table})").fetchall()
    return {row[1] for row in rows}
