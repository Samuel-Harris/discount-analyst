# Agent conversation

Completed Surveyor, Curator, and lane-agent nodes open a side panel with the stored system prompt, messages, and assistant response.

## Sub-features

- `conv-open-surveyor` opens the workflow Surveyor transcript from a completed `SURVEYOR` node.
- `conv-open-curator` opens the workflow Curator transcript from a completed `CURATOR` node.
- `conv-panel` shows heading `surveyor · workflow` (Surveyor), `curator · workflow` (Curator), or `{agent} · {ticker}` (lane agents) inside `Agent conversation`.
- `conv-close` dismisses the panel with `×` or Escape.

## How to get to it (user POV)

- On the pipeline graph, click a completed node labelled `SURVEYOR`, `CURATOR`, or a completed lane agent.
- Press Enter or Space while that node is focused.

## Driving it with verify-discount-analyst

Preconditions:

- `scripts/doctor` prints `OK`.
- `scripts/seed` has been run; `$RUN_ID` is the seeded id.
- Browser is on `$UI_URL/?run=$RUN_ID` (pipeline view).

- **Open Surveyor.** Click the completed `SURVEYOR` node. An aside named `Agent conversation` appears with heading `surveyor · workflow` and sections `System prompt`, `Messages`, `Assistant response`.
- **See seed prompt.** System prompt includes `seed surveyor system`.
- **Close.** Choose the panel `×` control (or press Escape). The aside is gone; the graph remains.
- **Open Curator.** Click the completed `CURATOR` node. The aside heading is `curator · workflow`. System prompt includes `seed curator system`.
- **Proof.** Snapshot and screenshot while Curator is open (`evidence/agent-conversation/open.aria.txt`, `open.png`) with `Agent conversation` and `seed curator system` visible.

## Gotchas

- Only `completed` nodes that are conversation agents are buttons. Skipped Appraiser on `SEED2.L` is not clickable.
- Graph nodes may lack accessible names. If click-by-name fails, use the snapshot ref for the `SURVEYOR` or `CURATOR` node or the clickable graph button near that label.
- Opening a node triggers `GET /api/agents/workflow_runs/$RUN_ID/agents/surveyor/conversation` (Surveyor), `GET /api/agents/workflow_runs/$RUN_ID/agents/curator/conversation` (Curator), or `GET /api/agents/runs/<run_id>/agents/<agent>/conversation` (lane agents). A 404 means the seed conversation is missing — re-seed on a fresh launch, do not use the developer database.
