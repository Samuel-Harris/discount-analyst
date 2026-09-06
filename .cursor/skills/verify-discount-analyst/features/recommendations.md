# Recommendations book and lane ratings

Recommendations replaces the pipeline graph with the Curator portfolio book above a sortable table of ticker lanes (rating, verdict source, entry path). Open it from the header or a deep link.

## Sub-features

- `rec-open-button` switches from the graph via `Recommendations`.
- `rec-deep-link` opens `?run=<id>&view=recommendations` directly.
- `rec-curator-book` shows the seeded Portfolio heading, cash strip, and `SEED1.L` in the book; omits unheld `SEED2.L` Avoid.
- `rec-filter` narrows lane-rating rows by ticker or company and does not hide book rows.
- `rec-reset-sort` returns to graph lane order via `Graph lane order`.

## How to get to it (user POV)

- With a run selected on the pipeline view, choose `Recommendations`.
- Open `$UI_URL/?run=<id>&view=recommendations`.
- From the table, choose `Pipeline graph` to leave the view.

## Driving it with verify-discount-analyst

Preconditions:

- `scripts/doctor` prints `OK`.
- `scripts/seed` has been run; `$RUN_ID` is the seeded workflow id from `GET $API_URL/api/workflow_runs`.

- **Open via deep link.** Navigate to `$UI_URL/?run=$RUN_ID&view=recommendations`. Heading `Portfolio` is present. A table caption `Final ratings and lane status for workflow $RUN_ID` is present (visually hidden). Toolbar shows `2 of 2 lane(s)`.
- **See the Curator book.** Rationale reads `Seed book: reduce the existing name and avoid the rejection.` Cash strip includes `20.0% → 85.0%` and band `84.0–86.0%`. `SEED1.L` is `Holding`, `Reduce`, `80.0% → 15.0%`, band `14.0–15.0%`. `SEED2.L` is not in the book (new Avoid). There is no `Clusters` heading.
- **See seed lane rows.** The `Lane ratings` table includes tickers `SEED1.L` and `SEED2.L`. Entry values are `Profiler` and `Surveyor`. `SEED2.L` shows verdict source `Sentinel`.
- **Filter.** In the `Filter` search box type `SEED2`. Count becomes `1 of 2 lane(s)` and `SEED1.L` is gone from the lane-ratings table. `SEED1.L` remains in the Portfolio book.
- **Clear filter.** Clear the search box. Both lane-rating rows return.
- **Button entry.** Navigate to `$UI_URL/?run=$RUN_ID` (pipeline), choose `Recommendations`. The book and table are shown again and the header button reads `Pipeline graph`.
- **Proof.** Screenshot and snapshot to `evidence/recommendations/table.png` and `table.aria.txt` with the Portfolio heading, `SEED1.L` in the book, and the Filter control visible.

## Gotchas

- `view=recommendations` without `run` is ignored; the app falls back to the pipeline empty state.
- `Graph lane order` is disabled until a column sort has been applied.
- Ratings and `Pending` are colour-coded; assert the cell text (`SEED1.L`, `Sentinel`), not the colour.
- Filter applies only to lane ratings, not to the Curator book.
- The book lists current holdings and names with a positive target weight. Unheld Avoid rows (seed `SEED2.L`) stay on the lane-ratings table only.
