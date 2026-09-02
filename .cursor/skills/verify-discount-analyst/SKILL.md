---
name: verify-discount-analyst
description: >-
  Drive the local Discount Analyst dashboard the way a user does: launch an
  isolated DEV API+Vite stack, exercise launch/sidebar/graph/recommendations/
  conversation, and capture proof. Use when verifying dashboard UI or API
  behaviour, proving a UI change works, or when asked to run
  verify-discount-analyst. Do not use for live LLM pipeline runs or CLI agent
  commands.
---

# Verify Discount Analyst

Drive the **dashboard** (Vite SPA + FastAPI) on an isolated DEV stack. The CLI (`uv run discount-analyst`) is a secondary surface: `--help` only. Never run `discount-analyst agent …` or `workflow run` as verification — those call live models.

There is no Playwright harness. Drive the UI with the Cursor IDE browser (navigate, snapshot, click, fill, screenshot) against the URL printed by `scripts/launch`. Confirm mutations with `curl` against the isolated API.

Read [features/README.md](features/README.md) before driving. A proof that hits one convenient entry point is incomplete when the map lists others.

## Launch

From the repository root:

```bash
.cursor/skills/verify-discount-analyst/scripts/launch
.cursor/skills/verify-discount-analyst/scripts/doctor
```

Ready when `doctor` prints `OK` and `GET $API_URL/api/workflow_runs` returns a JSON array. The UI is ready when `GET $UI_URL/` returns HTML titled `Discount Analyst — Dashboard`.

What launch does:

- Starts uvicorn (`discount_analyst.composition.api:create_app`) on `127.0.0.1:${VERIFY_API_PORT:-18080}` **without** `--reload`.
- Starts Vite on `127.0.0.1:${VERIFY_UI_PORT:-15173}` with `--strictPort`, proxying `/api` to that API.
- Forces `ENV=DEV` (mock mode locked in the launch form; FastAPI also forces `is_mock`).
- Uses sqlite `DASHBOARD_DATABASE_PATH=.cursor/artefacts/verify-discount-analyst/run/dashboard.verify.<run-id>.sqlite`.
- Sets `DASHBOARD_USE_TERMINAL=false`.

Still required from the repo `.env`: `LOGGING__LOGFIRE_API_KEY` and the other `Settings` keys. Launch does not create a `.env`.

Isolation:

- Default ports **18080** / **15173** so a developer dashboard on **8000** / **5173** / **8080** is left alone.
- Refuse to start if those verify ports are taken, or if `run/state.env` still points at live PIDs.
- **Never** open or click in a tab whose URL is not `$UI_URL` from `doctor`. Driving the user's session is forbidden.

Seed (optional; skip for empty-shell proofs):

```bash
.cursor/skills/verify-discount-analyst/scripts/seed
```

Inserts one completed mock workflow (`SEED1.L`, `SEED2.L`) via `discount_analyst.composition.dev_seed.seed`. Reload the UI afterwards.

Teardown is **Cleanup**, not a no-op.

## Doctor

```bash
.cursor/skills/verify-discount-analyst/scripts/doctor
```

Read-only. Run before the first drive, after anything surprising, and after a failed drive. It checks: recorded listen PIDs still running, those PIDs own the verify ports, sqlite basename is `dashboard.verify.*`, API list endpoint returns a JSON array, UI index title is `Discount Analyst — Dashboard`.

If doctor fails, stop driving. Read `run/api.log` / `run/ui.log`, then `scripts/cleanup` before another launch.

## Drive

1. `scripts/doctor` must be `OK`.
2. Open **`$UI_URL`** from that output in the Cursor browser. Snapshot. Confirm heading `Discount Analyst`, subtitle `Local pipeline dashboard · grouped workflow runs`, and badge `DEV`.
3. Follow the matching file under [features/](features/). Prefer accessible names: `Portfolio tickers`, `Start workflow`, `Recommendations`, `Pipeline graph`, `Agent conversation`. Sidebar run rows have **no** accessible name — identify them by the `mock` badge plus the short id, or deep-link `?run=<id>`.
4. Pair every user action with an observable result in the same step. For launches, `GET $API_URL/api/workflow_runs` is the persistence check; a screenshot alone is not.
5. Do not tick untick mock mode in DEV — the checkbox is locked.

Stable handles:

| Surface         | Handle                                                                                                              |
| --------------- | ------------------------------------------------------------------------------------------------------------------- |
| App identity    | heading `Discount Analyst`                                                                                          |
| Deploy env      | badge `DEV` (title `Dashboard deploy environment: DEV`)                                                             |
| Launch          | collapsed button `/Expand launch panel/`; expanded heading `Launch workflow`, textbox `Position ticker 1`, textbox `Also analyse`, button `Start workflow` |
| Sidebar         | text `Workflow runs`; collapse control title `Collapse sidebar`                                                     |
| Deep link       | `$UI_URL/?run=<workflow_run_id>` and `&view=recommendations`                                                        |
| Recommendations | button `Recommendations`; table caption `Final ratings and lane status for workflow <id>`; search labelled `Filter` |
| Conversation    | completed graph node (role `button`); complementary `Agent conversation`; close `×` or Escape                       |

## Evidence

Write under `.cursor/artefacts/verify-discount-analyst/evidence/<feature-id>/` (gitignored). Do not put proofs in `run/`.

Proof standard:

- Exercise the real UI path, not test-only endpoints. `POST /api/workflow_runs` is allowed as a **second** view of a launch the UI already performed, not as a substitute for clicking `Start workflow`.
- Capture the action **and** the resulting state (ARIA snapshot + screenshot with `Discount Analyst` visible).
- For mutations: a read-only second view (sidebar row, `GET /api/workflow_runs`, or reopen `?run=`).
- Record the feature ID and entry point in the artefact filenames or a `proof.txt` beside them.
- Mock pipeline stages sleep ~5s each. Launch proof is: the new run exists with `is_mock: true`. Do not wait for full completion unless the feature file says so.
- Never treat a skipped map entry as verified via a different path.

## Cleanup

```bash
.cursor/skills/verify-discount-analyst/scripts/cleanup
```

Kills only PIDs recorded in `run/state.env` (launch wrappers + listen PIDs). Deletes `run/` (sqlite, logs, state). **Leaves** `evidence/` in place.

After cleanup, confirm the evidence directory still exists. If a launch or drive fails mid-run, still run cleanup so ports and sqlite do not leak.

## Helpers

All paths are from the repository root. Scripts are executable.

| Command                                                  | What it does                                                                                                         |
| -------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| `.cursor/skills/verify-discount-analyst/scripts/launch`  | Isolated DEV API + Vite. Prints `UI_URL`, `API_URL`, `DATABASE_PATH`. Optional `VERIFY_API_PORT` / `VERIFY_UI_PORT`. |
| `.cursor/skills/verify-discount-analyst/scripts/doctor`  | Health check. Exit 0 only when the instance is ours and answering.                                                   |
| `.cursor/skills/verify-discount-analyst/scripts/seed`    | Completed mock workflow into the verify sqlite.                                                                      |
| `.cursor/skills/verify-discount-analyst/scripts/cleanup` | Stop those PIDs; remove `run/`; keep `evidence/`.                                                                    |

`scripts/lib.sh` and `scripts/spawn.py` are sourced/used by the others; do not invoke them directly.
