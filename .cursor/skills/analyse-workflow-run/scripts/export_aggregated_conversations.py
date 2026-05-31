"""Export agent conversations for one workflow run (stdlib only).

Writes one markdown file per agent under ``<output-dir>/aggregated_conversations/``:
workflow-scoped ``SURVEYOR``, then per-ticker agents ``PROFILER`` … ``APPRAISER``.

By default each file is **issue-focused**: transcripts are compressed (duplicate
system prompts, thinned ``user_prompt`` payloads, Appraiser-specific upstream
redaction when the prompt embeds ``ValuationResult``) and the aggregate is capped at **6,000 lines**, dropping the
lowest-scoring ticker sections first when the budget is exceeded. Heuristic
keyword scores approximate “which threads best illustrate recurring issues”
called out in workflow-run reviews (tool orchestration, rate limits, valuation
gates, post-DCF verdict / MoS themes, etc.).

Use ``--full-transcripts`` to restore the previous behaviour (no cap, no
compression).
"""

from __future__ import annotations

import argparse
import re
import sqlite3
from pathlib import Path
from typing import cast

ConversationSection = tuple[str, str, str, str]

PER_TICKER_AGENTS = (
    "PROFILER",
    "RESEARCHER",
    "STRATEGIST",
    "SENTINEL",
    "APPRAISER",
)

# Heuristic keyword bundles: higher hit counts → higher priority when trimming.
# Aligned with typical ``*_agent_review.md`` themes (tool noise, FMP stress,
# orchestration leakage, adversarial precision, DCF hand-off, final rating).
_AGENT_ISSUE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "SURVEYOR": (
        "fmp_search",
        "final_result",
        "multi_tool",
        "parallel",
        "web.",
        "orchestrat",
        "429",
        "402",
        "rate limit",
        "screen",
        "universe",
    ),
    "PROFILER": (
        "429",
        "402",
        "rate limit",
        "quota",
        "fmp_",
        "final_result",
        "multi_tool",
        "data_gaps",
        "red_flags",
        "web_search",
    ),
    "RESEARCHER": (
        "fmp_search",
        "symbol",
        ".LSE",
        ".L",
        "LON:",
        "multi_tool",
        "final_result",
        "DeepResearch",
        "429",
        "402",
        "source_notes",
    ),
    "STRATEGIST": (
        "final_result",
        "MispricingThesis",
        "mispricing",
        "orchestrator",
        "functions.",
        "evaluation_questions",
        "conviction",
        "falsif",
        "thesis",
    ),
    "SENTINEL": (
        "final_result",
        "EvaluationReport",
        "covenant",
        "stress",
        "material_data",
        "red_flag",
        "permanent_loss",
        "verdict",
        "confidence",
    ),
    "APPRAISER": (
        "final_result",
        "StockData",
        "StockAssumptions",
        "DCF",
        "valuation",
        "EvaluationReport",
        "429",
        "402",
        "fmp_",
        "lease",
        "net debt",
        "intrinsic",
        "bear_intrinsic",
        "bull_intrinsic",
        "base_intrinsic",
        "margin_of_safety",
        "STRONG BUY",
        "RatingTableDecision",
        "replicate bear",
        "identical",
        "scenario",
        "SELL",
        "large cap",
        "small-cap",
        "conviction",
    ),
}

_DEFAULT_MAX_LINES = 6000

_SYSTEM_PROMPT_BLOCK = re.compile(
    r"## System prompt\n\n```text\n([\s\S]*?)```\s*\n+(?=## Message 0)",
    re.MULTILINE,
)
_MSG0_SYSTEM_BLOCK = re.compile(
    r"### \(part\) system_prompt\n\n```text\n([\s\S]*?)```\s*\n+(?=### user_prompt)",
    re.MULTILINE,
)
_USER_PROMPT_BLOCK = re.compile(
    r"(### user_prompt\n\n)([\s\S]*?)(\n## Message \d+)",
    re.MULTILINE,
)
_UPSTREAM_BEFORE_VALUATION = re.compile(
    r"## StockCandidate\n\n<SurveyorCandidate>[\s\S]*?</EvaluationReport>\n\n---\n\n## ValuationResult\n\n",
    re.MULTILINE,
)
_UPSTREAM_BEFORE_VALUATION_REPL = (
    "## Upstream payloads (redacted)\n\n"
    "[Redacted — SurveyorCandidate, DeepResearchReport, MispricingThesis, and "
    "EvaluationReport JSON. ValuationResult below is preserved because single-point "
    "DCF outputs drive bear/base/bull behaviour in downstream MoS fields.]\n\n"
    "---\n\n## ValuationResult\n\n"
)


def _issue_keyword_score(agent: str, body: str) -> int:
    hay = body.lower()
    keys = _AGENT_ISSUE_KEYWORDS.get(agent, ())
    return sum(hay.count(k.lower()) for k in keys)


def _dedupe_message0_system(body: str) -> str:
    m_outer = _SYSTEM_PROMPT_BLOCK.search(body)
    m_inner = _MSG0_SYSTEM_BLOCK.search(body)
    if not m_outer or not m_inner:
        return body
    outer = m_outer.group(1).strip()
    inner = m_inner.group(1).strip()
    if outer != inner:
        return body
    stub = (
        "### (part) system_prompt\n\n"
        "```text\n"
        "[Redacted — duplicate of `## System prompt` above; present in Message 0 "
        "in the SQLite export.]\n"
        "```\n\n"
    )
    return body[: m_inner.start()] + stub + body[m_inner.end() :]


def _stub_outer_system_prompt(body: str) -> str:
    m = _SYSTEM_PROMPT_BLOCK.search(body)
    if not m:
        return body
    inner = m.group(1).strip()
    if len(inner) < 800:
        return body
    stub = (
        "## System prompt\n\n"
        "```text\n"
        "[Redacted — long investing creed + agent system instructions identical across "
        "tickers in this run. See digest export or `--full-transcripts` for verbatim "
        "text.]\n"
        "```\n\n"
    )
    return body[: m.start()] + stub + body[m.end() :]


def _thin_user_prompt(
    body: str,
    *,
    head_lines: int,
    tail_lines: int,
    min_lines_before_thin: int,
) -> str:
    def repl(match: re.Match[str]) -> str:
        prefix, content, suffix = match.group(1), match.group(2), match.group(3)
        lines = content.splitlines()
        if len(lines) <= min_lines_before_thin:
            return match.group(0)
        mid_omitted = len(lines) - head_lines - tail_lines
        if mid_omitted <= 0:
            return match.group(0)
        new_mid = (
            f"\n\n[... omitted {mid_omitted} lines of user_prompt — use "
            f"`conversation_digests/` or `--full-transcripts` for the full payload ...]\n\n"
        )
        new_content = (
            "\n".join(lines[:head_lines]) + new_mid + "\n".join(lines[-tail_lines:])
        )
        return prefix + new_content + suffix

    return _USER_PROMPT_BLOCK.sub(repl, body)


def _redact_upstream_before_valuation(body: str) -> str:
    if "## StockCandidate" not in body or "## ValuationResult" not in body:
        return body
    return _UPSTREAM_BEFORE_VALUATION.sub(_UPSTREAM_BEFORE_VALUATION_REPL, body)


def _compress_conversation_body(agent: str, body: str, *, full: bool) -> str:
    if full:
        return body
    out = body
    out = _dedupe_message0_system(out)
    out = _stub_outer_system_prompt(out)
    if agent == "APPRAISER":
        out = _redact_upstream_before_valuation(out)
        out = _thin_user_prompt(
            out, head_lines=60, tail_lines=60, min_lines_before_thin=120
        )
    else:
        out = _thin_user_prompt(
            out, head_lines=100, tail_lines=100, min_lines_before_thin=220
        )
    return out


def _format_conversation(
    con: sqlite3.Connection, conv_id: str, system_prompt: str
) -> str:
    lines: list[str] = [
        "## System prompt",
        "",
        "```text",
        (system_prompt or "").strip(),
        "```",
        "",
    ]
    rows = con.execute(
        """
        SELECT m.message_index, m.message_kind, p.part_index, p.part_kind,
               p.tool_name, p.tool_call_id, p.content_text
        FROM agent_conversation_messages m
        JOIN agent_conversation_message_parts p ON p.conversation_message_id = m.id
        WHERE m.conversation_id = ?
        ORDER BY m.message_index, p.part_index
        """,
        (conv_id,),
    ).fetchall()

    cur_msg: int | None = None
    for r in rows:
        mi, mk = r["message_index"], r["message_kind"]
        if mi != cur_msg:
            lines.extend(["", f"## Message {mi} (`{mk}`)", ""])
            cur_msg = mi
        pk = r["part_kind"]
        if pk == "text" and r["content_text"]:
            lines.extend([r["content_text"], ""])
        elif pk == "tool_call":
            tn = r["tool_name"] or "?"
            lines.append(f"### tool_call: `{tn}`")
            if r["tool_call_id"]:
                lines.append(f"- call_id: `{r['tool_call_id']}`")
            lines.extend(["", "```json", r["content_text"] or "", "```", ""])
        elif pk == "tool_return":
            tn = r["tool_name"] or "?"
            lines.extend(
                [
                    f"### tool_return: `{tn}`",
                    "",
                    "```",
                    r["content_text"] or "",
                    "```",
                    "",
                ]
            )
        elif pk == "retry_prompt":
            lines.append("### retry_prompt")
            if r["tool_name"]:
                lines.append(f"- tool: `{r['tool_name']}`")
            lines.extend(["", "```", r["content_text"] or "", "```", ""])
        elif pk == "system_prompt":
            lines.extend(
                [
                    "### (part) system_prompt",
                    "",
                    "```text",
                    (r["content_text"] or "").strip(),
                    "```",
                    "",
                ]
            )
        elif pk == "user_prompt":
            lines.extend(["### user_prompt", "", r["content_text"] or "", ""])
        else:
            lines.extend([f"### part `{pk}`", "", r["content_text"] or "", ""])

    return "\n".join(lines)


def _render_file_text(
    *,
    agent: str,
    workflow_id: str,
    sqlite_path: Path,
    sections: list[ConversationSection],
    curated: bool,
    line_budget: int | None = None,
    dropped_tickers: list[str] | None = None,
) -> str:
    """sections: (ticker, conversation_id, execution_id, body_markdown)."""
    budget = line_budget if line_budget is not None else _DEFAULT_MAX_LINES
    header: list[str] = [
        f"# {agent} conversations",
        "",
        f"- **workflow_run_id:** `{workflow_id}`",
        f"- **source_sqlite:** `{sqlite_path}`",
        f"- **conversations_included:** {len(sections)}",
        "",
    ]
    if curated:
        header.extend(
            [
                "> **Issue-focused aggregate:** duplicate system prompts are stubbed, "
                "large `user_prompt` bodies are head/tail thinned (Appraiser additionally "
                "redacts upstream JSON before `ValuationResult`). If the file would "
                f"exceed {budget} lines, entire ticker sections with the "
                "lowest heuristic keyword scores for this agent are dropped first. "
                "Re-run with `--full-transcripts` for uncapped verbatim exports.",
                "",
            ]
        )
    if dropped_tickers:
        header.append(
            "> **Tickers omitted for line budget (lowest keyword scores):** "
            + ", ".join(f"`{x}`" for x in dropped_tickers)
        )
        header.append("")
    chunks: list[str] = [*header]
    for ticker, conv_id, exec_id, body in sections:
        chunks.extend(
            [
                "---",
                "",
                f"## Ticker: `{ticker}`",
                "",
                f"- **conversation_id:** `{conv_id}`",
                f"- **execution_id:** `{exec_id}`",
                "",
                body,
                "",
            ]
        )
    return "\n".join(chunks).rstrip() + "\n"


def _line_count(s: str) -> int:
    return len(s.splitlines())


def _apply_line_budget(
    agent: str,
    sections: list[ConversationSection],
    *,
    max_lines: int,
    workflow_id: str,
    sqlite_path: Path,
) -> tuple[list[ConversationSection], list[str]]:
    """Drop lowest-scoring ticker bodies until the rendered file fits ``max_lines``."""

    def count(sec: list[ConversationSection]) -> int:
        text = _render_file_text(
            agent=agent,
            workflow_id=workflow_id,
            sqlite_path=sqlite_path,
            sections=sec,
            curated=True,
            line_budget=max_lines,
            dropped_tickers=None,
        )
        return _line_count(text)

    working = list(sections)
    dropped: list[str] = []
    while len(working) > 1 and count(working) > max_lines:
        scores = [
            (_issue_keyword_score(agent, b), t, i)
            for i, (t, _c, _e, b) in enumerate(working)
        ]
        scores.sort(key=lambda x: (x[0], x[1]), reverse=False)
        _score, drop_ticker, drop_idx = scores[0]
        dropped.append(drop_ticker)
        del working[drop_idx]
    guard = 0
    while len(working) == 1 and count(working) > max_lines and guard < 32:
        guard += 1
        t, c, e, b = working[0]
        prev_n = _line_count(b)
        b2 = _thin_user_prompt(
            b, head_lines=40, tail_lines=40, min_lines_before_thin=80
        )
        if b2 == b or _line_count(b2) >= prev_n:
            b2 = b[: max(0, len(b) // 2)] + "\n\n[... aggressively truncated ...]\n"
        working[0] = (t, c, e, b2)
    return working, dropped


def _write_file(
    path: Path,
    *,
    agent: str,
    workflow_id: str,
    sqlite_path: Path,
    sections: list[ConversationSection],
    full_transcripts: bool,
    max_lines: int,
) -> tuple[int, int]:
    """Returns ``(conversations_written, line_count)``."""
    if full_transcripts:
        text = _render_file_text(
            agent=agent,
            workflow_id=workflow_id,
            sqlite_path=sqlite_path,
            sections=sections,
            curated=False,
        )
        path.write_text(text, encoding="utf-8")
        return len(sections), _line_count(text)

    compressed: list[ConversationSection] = []
    for ticker, conv_id, exec_id, body in sections:
        b2 = _compress_conversation_body(agent, body, full=False)
        compressed.append((ticker, conv_id, exec_id, b2))
    final_sections, dropped = _apply_line_budget(
        agent,
        compressed,
        max_lines=max_lines,
        workflow_id=workflow_id,
        sqlite_path=sqlite_path,
    )
    text = _render_file_text(
        agent=agent,
        workflow_id=workflow_id,
        sqlite_path=sqlite_path,
        sections=final_sections,
        curated=True,
        line_budget=max_lines,
        dropped_tickers=dropped or None,
    )
    if _line_count(text) > max_lines:
        split = text.splitlines()
        keep = max(1, max_lines - 2)
        text = (
            "\n".join(split[:keep])
            + "\n\n> **Hard truncate:** file still exceeded line budget after compression; "
            "tail omitted. Use `--full-transcripts`.\n"
        )
    path.write_text(text, encoding="utf-8")
    return len(final_sections), _line_count(text)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export conversations per agent into aggregated_conversations/.",
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
    parser.add_argument(
        "--full-transcripts",
        action="store_true",
        help="Disable compression and line cap (legacy full export).",
    )
    parser.add_argument(
        "--max-lines",
        type=int,
        default=_DEFAULT_MAX_LINES,
        metavar="N",
        help=f"Maximum lines per agent markdown when not using --full-transcripts "
        f"(default: {_DEFAULT_MAX_LINES}).",
    )
    args = parser.parse_args()
    workflow_id: str = args.workflow_id
    db_path: Path = args.sqlite_path
    output_dir: Path = args.output_dir.resolve()
    full = args.full_transcripts
    max_lines: int = args.max_lines
    agg_dir = output_dir / "aggregated_conversations"
    agg_dir.mkdir(parents=True, exist_ok=True)

    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row

    surveyor = con.execute(
        """
        SELECT ac.id AS conversation_id, wae.id AS execution_id, ac.system_prompt
        FROM agent_conversations ac
        JOIN workflow_agent_executions wae ON wae.id = ac.workflow_agent_execution_id
        WHERE wae.workflow_run_id = ? AND wae.agent_name = 'SURVEYOR'
        """,
        (workflow_id,),
    ).fetchone()
    if surveyor:
        body = _format_conversation(
            con, surveyor["conversation_id"], surveyor["system_prompt"]
        )
        surveyor_sections: list[ConversationSection] = [
            (
                "__workflow__",
                surveyor["conversation_id"],
                surveyor["execution_id"],
                body,
            )
        ]
        n_conv, n_lines = _write_file(
            agg_dir / "SURVEYOR.md",
            agent="SURVEYOR",
            workflow_id=workflow_id,
            sqlite_path=db_path,
            sections=surveyor_sections,
            full_transcripts=full,
            max_lines=max_lines,
        )
        print(
            f"Wrote {agg_dir / 'SURVEYOR.md'} ({n_conv} conversations, {n_lines} lines)"
        )
    else:
        print("No SURVEYOR conversation for this workflow_run_id; skipped SURVEYOR.md")

    for agent in PER_TICKER_AGENTS:
        rows = con.execute(
            """
            SELECT r.ticker, ac.id AS conversation_id, ae.id AS agent_execution_id,
                   ac.system_prompt
            FROM runs r
            JOIN agent_executions ae ON ae.run_id = r.id AND ae.agent_name = ?
            JOIN agent_conversations ac ON ac.agent_execution_id = ae.id
            WHERE r.workflow_run_id = ?
            ORDER BY r.ticker
            """,
            (agent, workflow_id),
        ).fetchall()
        per_ticker_sections: list[ConversationSection] = []
        for r in rows:
            body = _format_conversation(con, r["conversation_id"], r["system_prompt"])
            per_ticker_sections.append(
                (
                    cast(str, r["ticker"]),
                    cast(str, r["conversation_id"]),
                    cast(str, r["agent_execution_id"]),
                    body,
                )
            )
        out = agg_dir / f"{agent}.md"
        n_conv, n_lines = _write_file(
            out,
            agent=agent,
            workflow_id=workflow_id,
            sqlite_path=db_path,
            sections=per_ticker_sections,
            full_transcripts=full,
            max_lines=max_lines,
        )
        print(
            f"Wrote {out} "
            f"({n_conv}/{len(per_ticker_sections)} conversations, {n_lines} lines)"
        )

    con.close()
    mode = "full transcripts" if full else f"issue-focused (≤{max_lines} lines)"
    print(f"Done ({mode}). Aggregated conversations under {agg_dir}")


if __name__ == "__main__":
    main()
