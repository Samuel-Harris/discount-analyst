"""Cluster FAILED/CANCELLED ticker lanes for a dashboard workflow run.

Read-only. Stdlib + rich. No writes to the SQLite file.
"""

from __future__ import annotations

import argparse
import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

from rich.console import Console
from rich.table import Table

_SECRET_QUERY_RE = re.compile(
    r"(?i)((?:api[_-]?token|api[_-]?key)=)([^&\s]+)",
)
_IN_SCOPE_RUN_STATUSES = frozenset({"failed", "cancelled"})
_IN_SCOPE_EXECUTION_STATUSES = frozenset({"failed", "cancelled"})
_EXPECTED_TABLES = (
    "workflow_runs",
    "runs",
    "agent_executions",
    "candidate_snapshots",
)

console = Console()


def redact_secrets(text: str | None) -> str:
    if not text:
        return ""
    return _SECRET_QUERY_RE.sub(r"\1<redacted>", text)


def classify_error(error_message: str | None) -> str:
    text = error_message or ""
    if not text.strip():
        return "empty"
    lowered = text.lower()
    if "schema must be an object" in lowered:
        return "tool_output_schema"
    if "dataqualityrejection" in lowered or "sentinelrejection" in lowered:
        return "persist_union"
    if "eodhdrealtimequote" in lowered:
        return "eodhd_payload"
    if "evaluationreport" in lowered or "material_data_gaps" in lowered:
        return "structured_output"
    if "web_fetch" in lowered or "max retries" in lowered:
        return "tool_retry_exhaustion"
    if "402" in text or "access denied" in lowered:
        return "vendor_plan"
    if "401" in text or "403" in text:
        return "http_auth"
    if "timeout" in lowered or "readtimeout" in lowered or "readerror" in lowered:
        return "timeout"
    if (
        "rate limit" in lowered
        or "tokens per min" in lowered
        or "tpm" in lowered
        or "too many requests" in lowered
    ):
        return "rate_limit"
    return "other"


def open_readonly(sqlite_path: Path) -> sqlite3.Connection:
    uri = f"file:{sqlite_path.resolve()}?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def table_columns(connection: sqlite3.Connection, table_name: str) -> set[str]:
    rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {row["name"] for row in rows}


def require_tables(connection: sqlite3.Connection) -> None:
    existing = {
        row["name"]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }
    missing = [name for name in _EXPECTED_TABLES if name not in existing]
    if missing:
        console.print(f"[red]Missing tables:[/red] {', '.join(missing)}")
        sys.exit(1)


def fetch_workflow(
    connection: sqlite3.Connection, workflow_id: str
) -> sqlite3.Row | None:
    columns = table_columns(connection, "workflow_runs")
    needed = {"id", "status", "started_at", "completed_at", "error_message"}
    missing = needed - columns
    if missing:
        console.print(
            f"[red]workflow_runs missing columns:[/red] {', '.join(sorted(missing))}"
        )
        sys.exit(1)
    return connection.execute(
        """
        SELECT id, status, started_at, completed_at, error_message
        FROM workflow_runs
        WHERE id = ?
        """,
        (workflow_id,),
    ).fetchone()


def fetch_runs(connection: sqlite3.Connection, workflow_id: str) -> list[sqlite3.Row]:
    columns = table_columns(connection, "runs")
    needed = {
        "ticker",
        "status",
        "entry_path",
        "error_message",
        "decision_type",
        "lane_aborted",
        "final_rating",
    }
    missing = needed - columns
    if missing:
        console.print(f"[red]runs missing columns:[/red] {', '.join(sorted(missing))}")
        sys.exit(1)
    return connection.execute(
        """
        SELECT ticker, status, entry_path, lane_aborted, decision_type,
               final_rating, error_message
        FROM runs
        WHERE workflow_run_id = ?
        ORDER BY ticker
        """,
        (workflow_id,),
    ).fetchall()


def fetch_executions(
    connection: sqlite3.Connection, workflow_id: str
) -> list[sqlite3.Row]:
    columns = table_columns(connection, "agent_executions")
    needed = {"agent_name", "status", "started_at", "error_message"}
    missing = needed - columns
    if missing:
        console.print(
            f"[red]agent_executions missing columns:[/red] {', '.join(sorted(missing))}"
        )
        sys.exit(1)
    return connection.execute(
        """
        SELECT COALESCE(r.ticker, '__workflow__') AS ticker,
               ae.agent_name, ae.status, ae.started_at, ae.error_message
        FROM agent_executions ae
        LEFT JOIN runs r ON ae.run_id = r.id
        WHERE ae.workflow_run_id = ?
           OR r.workflow_run_id = ?
        ORDER BY ticker, ae.started_at
        """,
        (workflow_id, workflow_id),
    ).fetchall()


def fetch_snapshots(
    connection: sqlite3.Connection, workflow_id: str
) -> list[sqlite3.Row]:
    columns = table_columns(connection, "candidate_snapshots")
    needed = {
        "ticker",
        "gate_status",
        "gate_failure_reason",
        "resolution_notes",
        "resolved_ticker",
        "gate_data_source",
    }
    missing = needed - columns
    if missing:
        console.print(
            f"[red]candidate_snapshots missing columns:[/red] {', '.join(sorted(missing))}"
        )
        sys.exit(1)
    return connection.execute(
        """
        SELECT cs.ticker, cs.gate_status, cs.gate_failure_reason,
               cs.resolved_ticker, cs.gate_data_source, cs.resolution_notes
        FROM candidate_snapshots cs
        JOIN agent_executions ae ON cs.agent_execution_id = ae.id
        LEFT JOIN runs r ON ae.run_id = r.id
        WHERE ae.workflow_run_id = ?
           OR r.workflow_run_id = ?
        ORDER BY cs.ticker
        """,
        (workflow_id, workflow_id),
    ).fetchall()


def print_header(workflow: sqlite3.Row, sqlite_path: Path) -> None:
    console.rule("Workflow")
    console.print(f"sqlite: {sqlite_path}")
    console.print(f"id: {workflow['id']}")
    console.print(f"status: {workflow['status']}")
    console.print(f"started_at: {workflow['started_at']}")
    console.print(f"completed_at: {workflow['completed_at']}")
    console.print(
        f"error_message: {redact_secrets(workflow['error_message']) or '(null)'}"
    )


def print_status_counts(runs: list[sqlite3.Row]) -> None:
    counts: dict[str, int] = defaultdict(int)
    for run in runs:
        counts[str(run["status"]).lower()] += 1
    table = Table(title="Lane status counts")
    table.add_column("status")
    table.add_column("count", justify="right")
    for status, count in sorted(counts.items()):
        table.add_row(status, str(count))
    table.add_row("total", str(len(runs)))
    console.print(table)


def in_scope_runs(runs: list[sqlite3.Row]) -> list[sqlite3.Row]:
    scoped: list[sqlite3.Row] = []
    for run in runs:
        status = str(run["status"]).lower()
        aborted = bool(run["lane_aborted"])
        if status in _IN_SCOPE_RUN_STATUSES or (aborted and status == "failed"):
            scoped.append(run)
    return scoped


def print_in_scope_lanes(runs: list[sqlite3.Row]) -> None:
    table = Table(title="In-scope lanes (FAILED / CANCELLED / lane_aborted+failed)")
    table.add_column("ticker")
    table.add_column("status")
    table.add_column("entry")
    table.add_column("kind")
    table.add_column("error")
    for run in runs:
        error_text = redact_secrets(run["error_message"])
        table.add_row(
            run["ticker"],
            str(run["status"]),
            str(run["entry_path"]),
            classify_error(run["error_message"]),
            error_text.replace("\n", " ")[:160] or "(empty)",
        )
    if not runs:
        console.print("[yellow]No FAILED/CANCELLED ticker lanes.[/yellow]")
        return
    console.print(table)


def print_error_buckets(runs: list[sqlite3.Row]) -> None:
    buckets: dict[str, list[str]] = defaultdict(list)
    for run in runs:
        buckets[classify_error(run["error_message"])].append(run["ticker"])
    table = Table(title="Error buckets (in-scope lanes)")
    table.add_column("kind")
    table.add_column("count", justify="right")
    table.add_column("tickers")
    for kind, tickers in sorted(
        buckets.items(), key=lambda item: (-len(item[1]), item[0])
    ):
        table.add_row(kind, str(len(tickers)), ", ".join(tickers))
    console.print(table)


def print_completed(runs: list[sqlite3.Row]) -> None:
    completed = [run for run in runs if str(run["status"]).lower() == "completed"]
    table = Table(title="COMPLETED lanes (not errors — count only)")
    table.add_column("ticker")
    table.add_column("decision_type")
    table.add_column("final_rating")
    for run in completed:
        table.add_row(
            run["ticker"],
            str(run["decision_type"] or ""),
            str(run["final_rating"] or ""),
        )
    console.print(f"Completed: {len(completed)}")
    if completed:
        console.print(table)


def print_executions(executions: list[sqlite3.Row]) -> None:
    in_scope = [
        row
        for row in executions
        if str(row["status"]).lower() in _IN_SCOPE_EXECUTION_STATUSES
    ]
    table = Table(title="In-scope agent executions (FAILED / CANCELLED)")
    table.add_column("ticker")
    table.add_column("agent")
    table.add_column("status")
    table.add_column("started_at")
    table.add_column("kind")
    table.add_column("error")
    for row in in_scope:
        error_text = redact_secrets(row["error_message"]).replace("\n", " ")[:160]
        table.add_row(
            row["ticker"],
            str(row["agent_name"]),
            str(row["status"]),
            str(row["started_at"] or ""),
            classify_error(row["error_message"]),
            error_text or "(empty)",
        )
    if not in_scope:
        console.print("[yellow]No FAILED/CANCELLED agent executions.[/yellow]")
        return
    console.print(table)


def print_snapshots(snapshots: list[sqlite3.Row], in_scope_tickers: set[str]) -> None:
    table = Table(title="Candidate snapshots (in-scope tickers)")
    table.add_column("ticker")
    table.add_column("gate")
    table.add_column("reason")
    table.add_column("source")
    table.add_column("notes")
    shown = 0
    for row in snapshots:
        if row["ticker"] not in in_scope_tickers:
            continue
        notes = redact_secrets(row["resolution_notes"]).replace("\n", " ")[:200]
        table.add_row(
            row["ticker"],
            str(row["gate_status"] or ""),
            str(row["gate_failure_reason"] or "")[:80],
            str(row["gate_data_source"] or ""),
            notes,
        )
        shown += 1
    if shown == 0:
        console.print("[yellow]No candidate snapshots for in-scope tickers.[/yellow]")
        return
    console.print(table)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read-only cluster of FAILED/CANCELLED lanes for a workflow UUID."
    )
    parser.add_argument("--workflow-id", required=True)
    parser.add_argument("--sqlite-path", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    sqlite_path: Path = args.sqlite_path
    if not sqlite_path.is_file():
        console.print(f"[red]SQLite file not found:[/red] {sqlite_path}")
        sys.exit(1)

    connection = open_readonly(sqlite_path)
    try:
        require_tables(connection)
        workflow = fetch_workflow(connection, args.workflow_id)
        if workflow is None:
            console.print(
                f"[red]0 rows[/red] for workflow_id={args.workflow_id} in {sqlite_path}. "
                "Stop and ask which database holds this UUID."
            )
            sys.exit(2)

        print_header(workflow, sqlite_path)
        runs = fetch_runs(connection, args.workflow_id)
        print_status_counts(runs)
        scoped_runs = in_scope_runs(runs)
        print_in_scope_lanes(scoped_runs)
        print_error_buckets(scoped_runs)
        print_completed(runs)
        executions = fetch_executions(connection, args.workflow_id)
        print_executions(executions)
        snapshots = fetch_snapshots(connection, args.workflow_id)
        print_snapshots(snapshots, {run["ticker"] for run in scoped_runs})
    finally:
        connection.close()


if __name__ == "__main__":
    main()
