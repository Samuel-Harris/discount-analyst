# Recommendations table

Recommendations replaces the pipeline graph with a sortable table of ticker lanes (rating, verdict source, entry path) and can be opened from the header or a deep link.

## Sub-features

- `rec-open-button` switches from the graph via `Recommendations`.
- `rec-deep-link` opens `?run=<id>&view=recommendations` directly.
- `rec-filter` narrows rows by ticker or company.
- `rec-reset-sort` returns to graph lane order via `Graph lane order`.

## How to get to it (user POV)

- With a run selected on the pipeline view, choose `Recommendations`.
- Open `$UI_URL/?run=<id>&view=recommendations`.
- From the table, choose `Pipeline graph` to leave the view.

## Driving it with verify-discount-analyst

Preconditions:

- `scripts/doctor` prints `OK`.
- `scripts/seed` has been run; `$RUN_ID` is the seeded workflow id from `GET $API_URL/api/workflow_runs`.

- **Open via deep link.** Navigate to `$UI_URL/?run=$RUN_ID&view=recommendations`. A table caption `Final ratings and lane status for workflow $RUN_ID` is present (visually hidden). Toolbar shows `2 of 2 lane(s)`.
- **See seed rows.** The table includes tickers `SEED1.L` and `SEED2.L`. Entry values are `Profiler` and `Surveyor`. `SEED2.L` shows verdict source `Sentinel`.
- **Filter.** In the `Filter` search box type `SEED1`. Count becomes `1 of 2 lane(s)` and `SEED2.L` is gone.
- **Clear filter.** Clear the search box. Both rows return.
- **Button entry.** Navigate to `$UI_URL/?run=$RUN_ID` (pipeline), choose `Recommendations`. The table is shown again and the header button reads `Pipeline graph`.
- **Proof.** Screenshot and snapshot to `evidence/recommendations/table.png` and `table.aria.txt` with both seed tickers and the Filter control visible.

## Gotchas

- `view=recommendations` without `run` is ignored; the app falls back to the pipeline empty state.
- `Graph lane order` is disabled until a column sort has been applied.
- Ratings and `Pending` are colour-coded; assert the cell text (`SEED1.L`, `Sentinel`), not the colour.
