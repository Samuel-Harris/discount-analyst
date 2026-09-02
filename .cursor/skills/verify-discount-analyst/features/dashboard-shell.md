# Dashboard shell

The dashboard identifies itself as Discount Analyst, shows that it is the DEV deploy, lists workflow runs in the sidebar, and leaves the main panel empty until a run is selected.

## Sub-features

- `shell-identity` shows the product heading and local-dashboard subtitle.
- `shell-dev-badge` shows the `DEV` deploy badge in the header (a `<span>`, not an ARIA role).
- `shell-empty-main` shows the select-or-launch placeholder when nothing is selected.
- `shell-launch-form` shows `Launch workflow` in the sidebar footer while the sidebar is expanded.

## How to get to it (user POV)

- Open the dashboard URL with no `?run=` query.
- Collapse then expand the sidebar with the `«` / `»` toolbar buttons (titles `Collapse sidebar` / `Expand runs`).

## Driving it with verify-discount-analyst

Preconditions:

- `scripts/launch` has started this run and `scripts/doctor` prints `OK`.
- `scripts/seed` has **not** been run (empty run list).
- The browser tab URL is exactly `$UI_URL` from doctor, with no query string.

- **Open the shell.** Navigate to `$UI_URL`. Snapshot. The heading is `Discount Analyst` and the subtitle is `Local pipeline dashboard · grouped workflow runs`.
- **Confirm DEV.** The mock checkbox label includes `required in DEV` and is checked and disabled. The header may also show a `DEV` badge; that badge has no ARIA role, so assert it from the screenshot.
- **Empty main panel.** The main region includes `Select a workflow run from the sidebar, or launch a new one from the launch panel.`
- **Launch form visible.** The sidebar includes heading `Launch workflow`, headings `Current positions` and `Also analyse`, textbox `Position ticker 1`, textbox `Cash in pounds`, textbox `Also analyse`, and button `Start workflow`. Mock mode text includes `Mock mode (required in DEV; no live LLM; slower simulated steps)`.
- **Proof.** Save an ARIA snapshot and a screenshot with the heading visible to `evidence/dashboard-shell/shell.aria.txt` and `evidence/dashboard-shell/shell.png`.

## Gotchas

- The header `DEV` badge is a span with no role, so ARIA snapshots omit it. Treat the locked mock-mode label (`required in DEV`) plus the screenshot as the DEV proof.
- `curl $UI_URL/` only proves the HTML shell (`Discount Analyst — Dashboard` in `<title>`). The heading and launch form exist only after React hydrates — use a browser snapshot.
- Ports 5173 / 8080 / 8000 are the developer’s usual stack. A tab there is not this instance.
- After `scripts/seed`, the main panel is still empty until a run is selected; the placeholder text remains valid only when `?run=` is absent.
