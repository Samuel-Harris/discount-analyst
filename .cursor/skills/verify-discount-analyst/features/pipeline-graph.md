# Pipeline graph

Selecting a workflow run shows a pipeline graph: a Surveyor node, one lane of agent nodes per ticker, and a workflow-level Curator node that the lanes feed into, with statuses on each node.

## Sub-features

- `graph-select-sidebar` opens a run from the sidebar list.
- `graph-deep-link` opens the same run via `?run=<id>`.
- `graph-seed-lanes` shows seeded tickers `SEED1.L` and `SEED2.L`, a `SURVEYOR` node, and a `CURATOR` node.

## How to get to it (user POV)

- Click a workflow row in the sidebar (`Workflow runs`).
- Open `$UI_URL/?run=<workflow_run_id>` with no `view` param (pipeline is the default).
- From Recommendations, choose `Pipeline graph`.

## Driving it with verify-discount-analyst

Preconditions:

- `scripts/doctor` prints `OK`.
- `scripts/seed` has been run once on this sqlite.
- `GET $API_URL/api/workflow_runs` returns at least one item; call that id `$RUN_ID`.

- **Deep-link the run.** Navigate to `$UI_URL/?run=$RUN_ID`. The detail header shows `id $RUN_ID`, a `mock` badge, and status `completed`.
- **See lanes.** The header includes `2 ticker lane(s)`. The graph shows a node labelled `SURVEYOR`, ticker tags `SEED1.L` and `SEED2.L`, and a node labelled `CURATOR`.
- **Sidebar selection.** The matching sidebar row is the active one (class `active` / selected styling).
- **Proof.** Screenshot and ARIA snapshot to `evidence/pipeline-graph/graph.png` and `graph.aria.txt` with `SURVEYOR`, `CURATOR`, and both seed tickers visible. Also save `curl -fsS $API_URL/api/workflow_runs/$RUN_ID` as `detail.json`.

## Gotchas

- React Flow nodes are often poor in the accessibility tree. If snapshot misses `SURVEYOR` or `CURATOR`, the screenshot plus `detail.json` (`runs[].ticker`, `curator_execution`) is the proof — say so in `proof.txt`.
- Completed conversation nodes are `role="button"`; incomplete nodes are not. Clicking the canvas background does nothing useful.
- Seed then launch creates extra rows. Select by full id from the API, not by list position.
