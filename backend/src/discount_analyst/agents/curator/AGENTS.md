<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-08-30 | Updated: 2026-09-06 -->

# curator

## Purpose

The `curator` directory contains the workflow-level Curator AI agent. After every ticker lane is terminal-success, it sizes a concentrated target portfolio from packed **valued** lane evidence and a current-position snapshot. It does not re-rate names. **Curator weights are the live recommendation.** Application code (`finalise_curator_proposal`) stamps current weights, company names, `source_run_id`, and `action`, then appends DQR zeros. `PortfolioAllocation` enforces totals and the 15% company cap. There is no allocation policy kind. Numbers are not repaired.

Curator is **not** a ticker-lane agent. It is a peer of Surveyor: one `AgentExecution` per workflow (`workflow_run_id` set, `run_id` null). Do not add it to `application/workflows/agent_lane_order.py`.

## Key Files

| File               | Description                                                                                                                                     |
| ------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| `curator.py`       | Factory for the Curator (`create_curator_agent`).                                                                                               |
| `schema.py`        | Self-contained `CuratorInput` / `CuratorProposal` plus field-identical `PackedMispricingThesis` (does not import Researcher–Appraiser schemas). |
| `system_prompt.py` | Concentrated best-ideas stance, packed-input contract, live web/terminal checks, and creed (no fixed holding period).                           |
| `user_prompt.py`   | `create_user_prompt(curator_input=...)`: tagged `CuratorInput` JSON; rank using `live_thesis`; `final_result` step.                             |
| `__init__.py`      | Package initialization for the curator module.                                                                                                  |

## Subdirectories

None.

## For AI Agents

### Working In This Directory

- **Agent tools**: `create_curator_agent` registers web search/fetch (factory default) and forwards `terminal`. It always passes `use_perplexity=False` and `use_mcp_financial_data=False`. `REGULATORY_TOOLSETS_BY_ROLE[CURATOR]` is empty. Dashboard Perplexity/MCP flags are not forwarded; terminal follows `settings.use_terminal` via `run_agent_with_terminal` on the dashboard and `--no-terminal` on the CLI. Frankfurter `convert_currency` remains attached by the shared factory; the prompt forbids calling it.
- **Schemas**: Keep `schema.py` free of imports from `agents.researcher`, `strategist`, `sentinel`, and `appraiser`. Application packing owns the compact-evidence mapping, including `live_thesis` (`PackedMispricingThesis`) on every valued lane. Do not invent or edit theses.
- **Output contract**: The LLM returns `CuratorProposal`. Persist `PortfolioAllocation` only after `finalise_curator_proposal` succeeds. Invalid weights fail the workflow; do not clip or normalise leftover weight into cash.

### Testing Requirements

- Mock dashboard and CLI paths live in `tests/backend/integration/test_mock_workflow.py` and allocation unit tests under `tests/backend/unit/`.
- Run tests using `uv run pytest`.

### Common Patterns

- **Structured I/O**: Callers build `CuratorInput` (dashboard assemble + CLI) and call `user_prompt.create_user_prompt`. One-shot CLI is `uv run discount-analyst agent curator <CuratorInput JSON>`.
- **Policy**: There is no packed rating or policy. Curator may size any weight on any valued lane, including adding to holdings and initiating new names, including 0%. Data-quality rejects are omitted from the LLM pack and stamped `[0,0,0]` afterwards. Keep the 15% company cap.

## Dependencies

### Internal

- `discount_analyst.agents.curator.schema`: `CuratorInput` and `CuratorProposal`.
- `discount_analyst.domain.allocations`: snapshot, invariants, and final `PortfolioAllocation`.
- `discount_analyst.config.ai_models_config`: model configuration.
- `discount_analyst.agents.runtime.agent_factory`: shared `create_agent` with web search/fetch, optional terminal, and no Perplexity/MCP/filings.

### External

- **pydantic-ai**: Agent framework.
- **pydantic**: Structured input and proposal models.

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
