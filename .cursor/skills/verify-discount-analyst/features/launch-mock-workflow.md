# Launch a mock workflow

Launch workflow lets a user enter current positions in pounds, optional also-analyse names, start a DEV mock run, and see that run appear in the sidebar without calling a live LLM.

## Sub-features

- `launch-add-position` records a holding ticker and pound value in the current-positions table.
- `launch-add-ticker` turns typed also-analyse text into a pill on Enter.
- `launch-start` creates a workflow and selects it in the main panel.
- `launch-mock-lock` keeps mock mode checked and the checkbox disabled in DEV.
- `launch-api` shows the same new id from `GET /api/workflow_runs`.

## How to get to it (user POV)

- Use the right-hand `Launch workflow` rail. It starts collapsed; choose `Expand launch panel` to edit holdings and also-analyse names.

## Driving it with verify-discount-analyst

Preconditions:

- `scripts/doctor` prints `OK` on an unseeded sqlite (or accept extra seed rows in the list).
- Browser is on `$UI_URL` with the left sidebar expanded.
- Expand the right launch rail with `Expand launch panel` so the current-positions table is visible.
- Note the current `GET $API_URL/api/workflow_runs` array length.

- **Confirm mock lock.** Snapshot. The mock checkbox is checked and disabled. Label text includes `required in DEV`.
- **Add a position.** Focus textbox `Position ticker 1`, type `VRFY.L`. Focus `Position value in pounds 1`, type `2500`. Focus `Cash in pounds`, replace the value with `500`.
- **Add an also-analyse name.** Focus textbox `Also analyse`, type `HINT.L`, press Enter. A pill `HINT.L` appears with a remove control named `Remove HINT.L`.
- **Start the run.** Choose `Start workflow`. The button may show `Starting…` then the main panel header shows a `mock` badge and a workflow `id …`.
- **Sidebar row.** The sidebar lists a new row with status `running` or `pending` and a `mock` badge. Deep link becomes `$UI_URL/?run=<id>`.
- **Confirm persistence.** `curl -fsS $API_URL/api/workflow_runs` includes an object whose `id` matches the header and `"is_mock": true`. Save that JSON to `evidence/launch-mock-workflow/runs.json`. `curl -fsS $API_URL/api/portfolio` returns `VRFY.L` in `positions` with `value_gbp` 2500, `cash_gbp` 500, and `HINT.L` in `suggestion_tickers`.
- **Proof.** Snapshot and screenshot the selected run (`evidence/launch-mock-workflow/after.aria.txt`, `after.png`) with `VRFY.L` still in the positions table or visible as a lane.

## Gotchas

- Empty book is allowed (Surveyor-only, 100% cash). This recipe enters a holding and cash so a Profiler lane is visible, plus an also-analyse pill.
- Draft also-analyse text is included even without Enter. If you type `HINT.L` and click `Start workflow` without Enter, the ticker is still submitted — do not require the pill for the API check, but the recipe above does press Enter.
- An in-progress position row is submitted only when both ticker and value are non-empty.
- Mock agent stages `asyncio.sleep(5)` each. Do **not** wait for `completed` unless you are explicitly proving completion; launch proof is the new `is_mock` row.
- Do not uncheck mock mode. In DEV the control is disabled; a PROD UI is the wrong instance.
- `POST /api/workflow_runs` is not a substitute for clicking `Start workflow`.
