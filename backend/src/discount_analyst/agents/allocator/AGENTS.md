<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-08-30 | Updated: 2026-08-30 -->

# allocator

## Purpose

The `allocator` directory contains the workflow-level Allocator AI agent. After every ticker lane is terminal-success, it sizes a concentrated target portfolio from packed lane evidence and a current-position snapshot. It does not re-rate names. Application code (`finalise_allocator_proposal`) stamps current weights, company names, policy, and `source_run_id`. `PortfolioAllocation` is the numeric gate (totals, 15% company cap, forced-zero / retain-or-reduce). Numbers are not repaired.

Allocator is **not** a ticker-lane agent. It is a peer of Surveyor: one `AgentExecution` per workflow (`workflow_run_id` set, `run_id` null). Do not add it to `application/workflows/agent_lane_order.py`.

## Key Files

| File               | Description                                                                                          |
| ------------------ | ---------------------------------------------------------------------------------------------------- |
| `allocator.py`     | Factory for the closed-book Allocator (`create_allocator_agent`).                                    |
| `schema.py`        | Self-contained `AllocatorInput` / `AllocatorProposal` (does not import Researcher–Appraiser schemas). |
| `system_prompt.py` | Concentrated best-ideas stance, closed-book rule, and creed (no fixed holding period).               |
| `user_prompt.py`   | `create_user_prompt(allocator_input=...)`: tagged `AllocatorInput` JSON plus `final_result` step.    |
| `__init__.py`      | Package initialization for the allocator module.                                                     |

## Subdirectories

None.

## For AI Agents

### Working In This Directory

- **Agent tools**: Closed book. `create_allocator_agent` always passes `enable_web_research_tools=False`, `use_perplexity=False`, `use_mcp_financial_data=False`, and disables the terminal session. `REGULATORY_TOOLSETS_BY_ROLE[ALLOCATOR]` is empty. Dashboard Perplexity/MCP/terminal flags are not forwarded. Frankfurter `convert_currency` remains attached by the shared factory; the prompt forbids calling it.
- **Schemas**: Keep `schema.py` free of imports from `agents.researcher`, `strategist`, `sentinel`, and `appraiser`. Application packing owns the compact-evidence mapping.
- **Output contract**: The LLM returns `AllocatorProposal`. Persist `PortfolioAllocation` only after `finalise_allocator_proposal` succeeds. Invalid weights fail the workflow; do not clip or normalise leftover weight into cash.

### Testing Requirements

- Mock dashboard and CLI paths live in `tests/backend/integration/test_mock_workflow.py` and allocation unit tests under `tests/backend/unit/`.
- Run tests using `uv run pytest`.

### Common Patterns

- **Structured I/O**: Callers build `AllocatorInput` (dashboard assemble + CLI) and call `user_prompt.create_user_prompt`. One-shot CLI is `uv run discount-analyst agent allocator <AllocatorInput JSON>`.
- **Policy**: Packed `policy` is authoritative. BUY/STRONG BUY = investable; existing HOLD = retain-or-reduce; new HOLD / SELL / STRONG SELL = forced-zero.

## Dependencies

### Internal

- `discount_analyst.agents.allocator.schema`: `AllocatorInput` and `AllocatorProposal`.
- `discount_analyst.domain.allocations`: snapshot, policy, invariants, and final `PortfolioAllocation`.
- `discount_analyst.config.ai_models_config`: model configuration.
- `discount_analyst.agents.runtime.agent_factory`: shared `create_agent` with closed-book flags.

### External

- **pydantic-ai**: Agent framework.
- **pydantic**: Structured input and proposal models.

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
