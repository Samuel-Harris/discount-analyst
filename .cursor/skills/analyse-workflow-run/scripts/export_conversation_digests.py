"""Export compact digests from dashboard SQLite for workflow run analysis (stdlib only)."""

from __future__ import annotations

import argparse
import sqlite3
from collections import defaultdict
from pathlib import Path


def digest_one(
    con: sqlite3.Connection,
    *,
    agent: str,
    ticker: str,
    conv_id: str,
    out_dir: Path,
) -> None:
    parts = con.execute(
        """
        SELECT m.message_index, m.message_kind, p.part_index, p.part_kind,
               p.content_text, p.tool_name, p.tool_call_id
        FROM agent_conversation_messages m
        JOIN agent_conversation_message_parts p ON p.conversation_message_id = m.id
        WHERE m.conversation_id = ?
        ORDER BY m.message_index, p.part_index
        """,
        (conv_id,),
    ).fetchall()

    text_chunks: list[str] = []
    tool_calls: list[str] = []
    for p in parts:
        if p["part_kind"] == "text" and p["content_text"]:
            text_chunks.append(p["content_text"])
        if p["part_kind"] == "tool_call":
            name = p["tool_name"] or "?"
            raw = (p["content_text"] or "")[:800]
            tool_calls.append(
                f"{name}: {raw[:200]}…" if len(raw) > 200 else f"{name}: {raw}"
            )
        if p["part_kind"] == "tool_return":
            tool_calls.append(f"return({p['tool_name']})")

    combined = "\n\n".join(text_chunks)
    tail = combined[-12000:] if len(combined) > 12000 else combined
    head = combined[:4000] if len(combined) > 12000 else ""

    lines = [
        f"# {agent} | {ticker}",
        f"conversation_id={conv_id}",
        f"parts={len(parts)} text_chars={len(combined)}",
        "",
        "## Tool surface",
        *(tool_calls[:40] or ["(none)"]),
        "",
        "## Text (head)" if head else "## Text",
    ]
    if head:
        lines.append(head)
        lines.extend(["", "## Text (tail — most recent model prose)"])
    lines.append(tail)

    safe_t = ticker.replace(".", "_")
    fname = f"{agent}_{safe_t}.md"
    (out_dir / fname).write_text("\n".join(lines), encoding="utf-8")


def merge_by_agent(out_dir: Path) -> None:
    by_agent: dict[str, list[Path]] = defaultdict(list)
    for p in sorted(out_dir.glob("*.md")):
        if p.name.startswith("_"):
            continue
        agent = p.name.split("_", 1)[0]
        by_agent[agent].append(p)

    for agent, paths in sorted(by_agent.items()):
        chunks = [f"# All digests: {agent}\n"]
        for path in paths:
            chunks.append(f"\n---\n\n## File: `{path.name}`\n\n")
            chunks.append(path.read_text(encoding="utf-8"))
        (out_dir / f"_MERGED_{agent}.md").write_text("".join(chunks), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export conversation digests for a dashboard workflow run.",
    )
    parser.add_argument(
        "--workflow-id",
        required=True,
        help="workflow_runs.id (UUID)",
    )
    parser.add_argument(
        "--sqlite-path",
        required=True,
        type=Path,
        help="Path to dashboard SQLite (e.g. data/dashboard.sqlite or artefact copy)",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        type=Path,
        help="Per-run artefact directory "
        "(e.g. .cursor/artefacts/analyse-workflow-run/<uuid>/)",
    )
    args = parser.parse_args()
    workflow_id: str = args.workflow_id
    db_path: Path = args.sqlite_path
    output_dir: Path = args.output_dir.resolve()
    digest_dir = output_dir / "conversation_digests"
    digest_dir.mkdir(parents=True, exist_ok=True)

    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row

    rows = con.execute(
        """
        SELECT ac.id AS conv_id, wae.agent_name
        FROM agent_conversations ac
        JOIN workflow_agent_executions wae ON wae.id = ac.workflow_agent_execution_id
        WHERE wae.workflow_run_id = ?
        """,
        (workflow_id,),
    ).fetchall()
    for r in rows:
        digest_one(
            con,
            agent=r["agent_name"],
            ticker="__workflow__",
            conv_id=r["conv_id"],
            out_dir=digest_dir,
        )

    rows = con.execute(
        """
        SELECT ae.agent_name, r.ticker, ac.id AS conv_id
        FROM agent_conversations ac
        JOIN agent_executions ae ON ae.id = ac.agent_execution_id
        JOIN runs r ON r.id = ae.run_id
        WHERE r.workflow_run_id = ?
        ORDER BY ae.agent_name, r.ticker
        """,
        (workflow_id,),
    ).fetchall()
    for r in rows:
        digest_one(
            con,
            agent=r["agent_name"],
            ticker=r["ticker"],
            conv_id=r["conv_id"],
            out_dir=digest_dir,
        )

    con.close()
    merge_by_agent(digest_dir)
    print(f"Wrote digests under {digest_dir}")


if __name__ == "__main__":
    main()
