# Launch a mock workflow

Launch workflow lets a user add portfolio tickers, start a DEV mock run, and see that run appear in the sidebar without calling a live LLM.

## Sub-features

- `launch-add-ticker` turns typed text into a pill on Enter.
- `launch-start` creates a workflow and selects it in the main panel.
- `launch-mock-lock` keeps mock mode checked and the checkbox disabled in DEV.
- `launch-api` shows the same new id from `GET /api/workflow_runs`.

## How to get to it (user POV)

- Use the `Launch workflow` panel in the expanded sidebar.
- If the sidebar is collapsed, the same form appears under the main panel.

## Driving it with verify-discount-analyst

Preconditions:

- `scripts/doctor` prints `OK` on an unseeded sqlite (or accept extra seed rows in the list).
- Browser is on `$UI_URL` with the sidebar expanded.
- Note the current `GET $API_URL/api/workflow_runs` array length.

- **Confirm mock lock.** Snapshot. The mock checkbox is checked and disabled. Label text includes `required in DEV`.
- **Add a ticker.** Focus textbox `Portfolio tickers`, type `VRFY.L`, press Enter. A pill `VRFY.L` appears with a remove control named `Remove VRFY.L`.
- **Start the run.** Choose `Start workflow`. The button may show `Starting…` then the main panel header shows a `mock` badge and a workflow `id …`.
- **Sidebar row.** The sidebar lists a new row with status `running` or `pending` and a `mock` badge. Deep link becomes `$UI_URL/?run=<id>`.
- **Confirm persistence.** `curl -fsS $API_URL/api/workflow_runs` includes an object whose `id` matches the header and `"is_mock": true`. Save that JSON to `evidence/launch-mock-workflow/runs.json`.
- **Proof.** Snapshot and screenshot the selected run (`evidence/launch-mock-workflow/after.aria.txt`, `after.png`) with `VRFY.L` still in the launch pills or visible as a lane.

## Gotchas

- Empty portfolio is allowed (Surveyor-only). Launching with no tickers still creates a run; this recipe uses `VRFY.L` so a Profiler lane is visible.
- Draft text is included even without Enter. If you type `VRFY.L` and click `Start workflow` without Enter, the ticker is still submitted — do not require the pill for the API check, but the recipe above does press Enter.
- Mock agent stages `asyncio.sleep(5)` each. Do **not** wait for `completed` unless you are explicitly proving completion; launch proof is the new `is_mock` row.
- Do not uncheck mock mode. In DEV the control is disabled; a PROD UI is the wrong instance.
- `POST /api/workflow_runs` is not a substitute for clicking `Start workflow`.
