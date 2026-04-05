<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-04-05 -->

# arbiter

## Purpose

The Arbiter agent synthesises Surveyor context, Researcher evidence, Strategist thesis, Sentinel evaluation, and `ValuationResult` (Appraiser + DCF) into a single `ArbiterDecision`. It is the only stage that receives `is_existing_position`, and that flag affects **recommended_action framing only**, not the rating.

## Key Files

| File               | Description                                                                                                         |
| ------------------ | ------------------------------------------------------------------------------------------------------------------- |
| `arbiter.py`       | `create_arbiter_agent` (no web/MCP tools).                                                                          |
| `schema.py`        | `ArbiterInput`, `ValuationResult`, `ArbiterDecision` (`rating`: `InvestmentRating` from `discount_analyst.rating`). |
| `system_prompt.py` | Synthesis-only stance and gating reminders.                                                                         |
| `user_prompt.py`   | `create_user_prompt`: serialised upstream JSON sections.                                                            |
| `__init__.py`      | Public exports.                                                                                                     |

## For AI Agents

- **No tools**: Same pattern as Strategist/Sentinel; do not enable search or MCP here.
- **Downstream**: Workflow wraps `ArbiterDecision` in `discount_analyst.pipeline.Verdict` for human-facing output.

## Dependencies

- Upstream stage schemas: `surveyor`, `researcher`, `strategist`, `sentinel`, `appraiser`, `valuation.data_types`.
