# Analyse workflow run — artefact layout

All artefacts for one analysis share:

`.cursor/artefacts/analyse-workflow-run/<workflow-run-id>/`

Do not place run-specific SQLite copies, digests, or final reports beside each other at the parent `.cursor/artefacts/analyse-workflow-run/` level — always nest by UUID.

## Copying SQLite from the host dashboard

The dashboard API uses host SQLite by default (`data/dashboard.sqlite`, overridable via `DASHBOARD_DATABASE_PATH` in `.env`). Copy the live file before analysis:

```bash
cp data/dashboard.sqlite \
  ".cursor/artefacts/analyse-workflow-run/<workflow-run-id>/dashboard.sqlite"
```

Stop the API first if you need a consistent snapshot while writes are in flight.

## Digest export

Script (stdlib only, no repo imports):

`.cursor/skills/analyse-workflow-run/scripts/export_conversation_digests.py`

- `--workflow-id` (required)
- `--sqlite-path` (required): path to the dashboard SQLite file
- `--output-dir` (required): the `<workflow-run-id>/` directory; creates `conversation_digests/` inside it

## Aggregated conversations (transcripts)

Script (stdlib only, no repo imports):

`.cursor/skills/analyse-workflow-run/scripts/export_aggregated_conversations.py`

- Required flags: same three as digest export (`--workflow-id`, `--sqlite-path`, `--output-dir`).
- Optional: **`--full-transcripts`** — disable compression and line cap (verbatim export, previous default).
- Optional: **`--max-lines N`** — per-agent line cap when curated (default **6000**).
- Creates `<workflow-run-id>/aggregated_conversations/` with one markdown file per agent: `SURVEYOR.md` (workflow-scoped, if present) and `PROFILER.md`, `RESEARCHER.md`, `STRATEGIST.md`, `SENTINEL.md`, `APPRAISER.md` (each file contains ticker sections in ticker order).
- **Default (curated):** stubs duplicate system prompts, thins huge `user_prompt` blocks (Appraiser also redacts upstream JSON before `ValuationResult` when that pattern appears), then enforces the line cap by **omitting** lowest-scoring ticker threads first (heuristic keywords aligned with typical workflow-run review themes). Header blockquotes list any omitted tickers.
- Use **`--full-transcripts`** for audit trails that need every line; use **default** for grep-friendly issue-focused review; use `conversation_digests/` for token-efficient merged digests in subagent step 6.
