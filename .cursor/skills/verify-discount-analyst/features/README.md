# Discount Analyst verification map

This directory is the maintained source for verifying the user-facing behaviour of the Discount Analyst **dashboard**. Read the index before driving the app, then use the matching feature file as the recipe.

## Baseline preconditions

- Launch with `.cursor/skills/verify-discount-analyst/scripts/launch` so the UI is at `http://127.0.0.1:15173` (or `$VERIFY_UI_PORT`) and the API at `http://127.0.0.1:18080` (or `$VERIFY_API_PORT`).
- Sqlite must be the verify file from `scripts/doctor` (`dashboard.verify.<run-id>.sqlite`). Never point at `data/dashboard.sqlite`, `data/dashboard.dev.sqlite`, or `data/dashboard.prod.sqlite`.
- `ENV=DEV`: mock mode is required; do not attempt a live LLM run from this stack.
- Run `scripts/doctor` and require `OK`, the printed `UI_URL` / `API_URL`, and a `dashboard.verify.*` database path.
- Never drive an instance that was not started by this verification run. Ignore tabs on ports 5173, 8000, and 8080.

## Driving conventions

- Start every recipe from the baseline state unless its preconditions say otherwise. Seed only when the feature file says so.
- Prefer ARIA roles and accessible names over CSS selectors or coordinates.
- Treat every command as literal. Keep quoted names and flags unchanged.
- Browser: Cursor IDE browser against `$UI_URL` from doctor (navigate, snapshot, click, fill, screenshot).
- HTTP checks: `curl` against `$API_URL` from doctor.
- Restore disposable runs after a mutation when the feature says to. Do not remove proof artefacts during cleanup.

## Proof and skip reporting

- Capture the user action and the resulting state, not only the final screen.
- UI proof includes an ARIA snapshot and a screenshot with the heading `Discount Analyst` visible.
- Mutation proof includes a read-only second view (`GET /api/workflow_runs` or reopen `?run=`).
- Record the feature ID and entry point used with every artefact.
- Report an unreachable path with the attempted command and the unmet precondition.
- Do not report a skipped entry point as verified through a different path.

## Feature entry contract

Each feature file starts with an H1 title and one paragraph describing the user-visible behaviour. It then uses exactly four H2 sections in this order.

1. `Sub-features` lists short IDs with one line for each behaviour.
2. `How to get to it (user POV)` lists every user entry point.
3. `Driving it with verify-discount-analyst` starts with `Preconditions:` and uses labeled bullets that pair each user action with an exact command and observable result.
4. `Gotchas` lists traps that can waste or invalidate a verification run.

Keep implementation details out of the map. Name only user paths, stable handles, required state, commands, and observable proof.

## Features

- [Dashboard shell](./dashboard-shell.md) covers identity, DEV badge, empty main panel, sidebar, and launch form visibility.
- [Launch a mock workflow](./launch-mock-workflow.md) covers current positions, also-analyse pills, Start workflow, mock lock, and the new sidebar row.
- [Pipeline graph](./pipeline-graph.md) covers selecting a seeded run and seeing Surveyor plus ticker lanes.
- [Recommendations table](./recommendations.md) covers the Recommendations view, filter, sort reset, and the `?view=recommendations` deep link.
- [Agent conversation](./agent-conversation.md) covers opening a completed node’s transcript panel and closing it.
