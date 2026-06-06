# Analyse workflow run — artefact layout

All artefacts for one analysis share:

`.cursor/artefacts/analyse-workflow-run/<workflow-run-id>/`

Do not place run-specific SQLite copies, digests, or final reports beside each other at the parent `.cursor/artefacts/analyse-workflow-run/` level — always nest by UUID.

## Copying SQLite from the host dashboard

Saved production workflow runs live in **`data/dashboard.prod.sqlite`** (VS Code PROD stack sets `DASHBOARD_DATABASE_PATH=data/dashboard.prod.sqlite`). Copy before analysis:

```bash
cp data/dashboard.prod.sqlite \
  ".cursor/artefacts/analyse-workflow-run/<workflow-run-id>/dashboard.sqlite"
```

Verify the workflow exists:

```sql
SELECT id, status, started_at FROM workflow_runs WHERE id = '<workflow-run-id>';
```

Other host files: `data/dashboard.dev.sqlite` (DEV stack), `data/dashboard.sqlite` (config default when env unset). Stop the API first if you need a consistent snapshot while writes are in flight.

## Digest export

Script (stdlib only, no repo imports):

`.cursor/skills/analyse-workflow-run/scripts/export_conversation_digests.py`

- `--workflow-id` (required)
- `--sqlite-path` (required): path to the dashboard SQLite file
- `--output-dir` (required): the `<workflow-run-id>/` directory; creates `conversation_digests/` inside it

Output:

- Per-conversation `{AGENT}_{ticker}.md` (Surveyor workflow conversation → `SURVEYOR___workflow__.md`).
- `_MERGED_{AGENT}.md` for each agent with conversations (names are **uppercase** in production SQLite).

## Aggregated conversations (transcripts)

Script (stdlib only, no repo imports):

`.cursor/skills/analyse-workflow-run/scripts/export_aggregated_conversations.py`

- Required flags: same three as digest export (`--workflow-id`, `--sqlite-path`, `--output-dir`).
- Optional: **`--full-transcripts`** — disable compression and line cap (verbatim export).
- Optional: **`--max-lines N`** — per-agent line cap when curated (default **6000**).
- Creates `<workflow-run-id>/aggregated_conversations/` with one markdown file per agent: `SURVEYOR.md` (workflow-scoped, if present) and `PROFILER.md`, `RESEARCHER.md`, `STRATEGIST.md`, `SENTINEL.md`, `APPRAISER.md` (each file contains ticker sections in ticker order).
- **Default (curated):** stubs duplicate system prompts, thins huge `user_prompt` blocks (Appraiser also redacts upstream JSON before `ValuationResult` when that pattern appears), then enforces the line cap by **omitting** lowest-scoring ticker threads first (heuristic keywords aligned with typical workflow-run review themes). Header blockquotes list any omitted tickers.
- Use **`--full-transcripts`** for audit trails that need every line; use **default** for grep-friendly issue-focused review; use `conversation_digests/` for token-efficient merged digests in subagent step 6.
