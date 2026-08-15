---
name: sync-workflow
description: >-
  Investigates the Discount Analyst codebase (agents, Pydantic schemas,
  orchestration, gates, tools/MCP/data sources) and regenerates
  current_workflow.md from ground truth in the code — not from memory of the
  doc. Use whenever the user asks to refresh, audit, or sync the workflow doc;
  asks whether current_workflow.md is stale or out of date; asks what the
  pipeline "actually does now"; wants to discuss architecture, schema, or agent
  design without reading code themselves; or asks for a pipeline/schema summary
  before a strategy or product discussion. Also trigger proactively after the
  user mentions adding/removing an agent, changing a schema, or editing
  orchestration logic — offer to re-sync the doc.
---

# Discount Analyst — Workflow Doc Sync

## Purpose

`current_workflow.md` is a hand-maintained snapshot of an agentic pipeline. Hand-maintained docs drift. This skill turns doc refresh into an investigation task: read the actual code that defines agents, schemas, and orchestration, and regenerate the doc so it matches reality — flagging every place the old doc and the code disagreed.

**Ground truth is always the code.** If a prompt, a comment, or the previous doc says one thing and the code does another, the code wins, and the disagreement gets called out explicitly rather than silently resolved.

This skill requires an agent with filesystem/bash access to the actual repository (Claude Code, Cowork, or similar). It cannot run from chat alone without the repo attached.

## When NOT to regenerate the whole doc

If the user just wants to know one fact ("what does the Sentinel gate check again?"), answer it directly from the current doc or a quick targeted code read. Reserve the full procedure below for "sync/refresh/audit the doc" requests or when you suspect drift.

---

## Step-by-step procedure

### 1. Locate the anchors

Start from the known anchor files (confirm each still exists at these paths — repo layout may have moved things since the doc was last written; if a path is gone, search for its replacement rather than assuming it was deleted):

| Concern                       | Last known location                                                            |
| ----------------------------- | ------------------------------------------------------------------------------ |
| Dashboard orchestration       | `backend/pipeline/sqlmodel_runner.py` (`DashboardPipelineRunner`)              |
| Workflow HTTP API             | `backend/routers/workflow_runs.py`                                             |
| CLI full pipeline             | `scripts/workflows/run_full_workflow.py`                                       |
| Verdict builders / gate logic | `discount_analyst/pipeline/builders.py`, `discount_analyst/pipeline/schema.py` |
| Agent lane order              | `backend/contracts/agent_lane_order.py`                                        |
| Per-agent prompts + schema    | `discount_analyst/agents/<agent>/`                                             |
| Rating enum                   | `discount_analyst/rating.py`                                                   |

Then do a fresh discovery pass so new agents/stages aren't missed:
```bash
find . -path '*/agents/*/schema.py'
grep -rl "class .*Agent" --include=*.py .
grep -rln "BaseModel" --include=*.py discount_analyst/ backend/
```
Any schema or agent directory not in the table above is new since the doc was last synced — note it explicitly in the output.

### 2. Enumerate agent stages

For each agent directory (`discount_analyst/agents/<agent>/`), read:
- The **prompt file(s)** (system/user) — extract the agent's stated *stance* (e.g. "neutral evidence assembler" vs "adversary, not validator") and what it says its input/output is.
- The **factory function** that builds it (e.g. `create_surveyor_agent`) — this is where model choice, tools, and any MCP/data-source wiring live.
- Cross-check the prompt's own description of its output schema against the *actual* schema class it's bound to in code. Stale terminology here (prompt says one model name, code enforces another) is a known drift pattern — flag it, don't silently correct it.

### 3. Extract the schema reference programmatically

Do not hand-read `schema.py` files for field lists — introspect the live Pydantic models instead, so nothing is missed or misremembered. For each schema module found in step 1:

```bash
python3 - <<'PY'
import importlib, json

module_path = "discount_analyst.agents.researcher.schema"   # repeat per module
mod = importlib.import_module(module_path)

for name in dir(mod):
    obj = getattr(mod, name)
    if hasattr(obj, "model_json_schema"):
        print(f"--- {name} ---")
        print(json.dumps(obj.model_json_schema(), indent=2))
PY
```
`model_json_schema()` gives exact field names, types, required-vs-optional, defaults, `description`, and constraints (`minLength`, `minItems`, `ge`/`le`, etc.) straight from the class definition. For plain enums, print `list(EnumClass)` or `{e.name: e.value for e in EnumClass}` to get the authoritative allowed-values list — don't transcribe enum values from memory or from the old doc.

Do this for every model that crosses an agent boundary or gets persisted (mirror the "Complete schema reference" section of the existing doc — one entry per model, not a partial list).

### 4. Trace orchestration and gates

Read the actual control-flow code, not a description of it:
- `DashboardPipelineRunner` (or its current equivalent) — the literal sequence of stages, what's parallel vs serial, and why (e.g. rate-limit avoidance).
- Every programmatic gate function (e.g. `sentinel_proceeds_to_valuation`) — read the real conditional, don't infer it from a function name. Note the exact boolean logic.
- Every place a stage can be **skipped** or a lane can **short-circuit** (e.g. `SentinelRejection` construction, DCF failure handling) — these are easy to miss because they're not on the "happy path."
- How `is_existing_position` (or its current equivalent flag distinguishing new candidates from portfolio review) is threaded through — confirm whether it still only affects wording, or whether it now affects rating-tier logic. This is a meaningful policy question worth flagging either way.

Regenerate the pipeline diagram (mermaid) from this trace, not from the old diagram.

### 5. Inventory data and tools available to agents

This is the part most likely to be invisible from schemas alone — check explicitly:
- Which agents call **web search / Perplexity / any research API**, and how that's configured (settings flags, per-agent config).
- Any **MCP servers** wired to specific agents — grep for `mcp_servers`, tool registration, or connector config.
- Any **deterministic calculation engines** invoked outside the LLM path (e.g. the DCF engine) — confirm inputs/outputs still match what's documented.
- **Mock/stub mode** (`is_mock` or equivalent) — confirm what triggers it and what agents do differently when it's on, since this affects whether "the pipeline ran" actually means live data was used.
- Model/provider selection per agent, if configurable — note where this lives (settings file) rather than hardcoding assumed values into the doc.

### 6. Diff against the existing doc

Locate the current doc (commonly at the repo root; search if not there). For each section, note concretely:
- Schemas: fields added, removed, renamed, or with changed constraints/enum values.
- Agents: any added, removed, renamed, or re-scoped.
- Gates/orchestration: any changed conditions, new short-circuit paths, changed skip behaviour.
- Ratings: any change to the enum values or to how `SentinelRejection`/`ArbiterDecision` derive them.
- Tools/data: anything new or removed per step 5.

If nothing changed in a section, say so briefly rather than omitting it — silence reads as "not checked."

### 7. Write the refreshed doc

Regenerate the full doc, mirroring the structure of the existing one (Overview → pipeline diagram → agent handoff table → rating system → complete schema reference → per-stage sections → data flow summary → design principles → "where to look in the repo"). Keep the same register: implementation-accurate but readable without an IDE open, since its purpose is letting the user reason about the system without reading code.

Lead the doc (or your chat response — whichever the user will see first) with a short **"Changes since last sync"** callout summarising step 6's findings. This is usually the most useful part for a discussion — the full doc is the reference underneath it.

Save the regenerated doc over the existing file so version control captures the diff naturally. If no prior doc exists, create it at the repo root using the same filename convention.

### 8. Sanity pass before handing back

- Every field/enum in the schema reference should trace to a `model_json_schema()` call or enum introspection from step 3 — not to your own recollection of the previous doc.
- Every orchestration claim should trace to a specific file/function read in step 4.
- Anything you couldn't verify statically (e.g., true runtime behaviour of a feature flag that depends on env vars you can't see) — say so explicitly and point to where the user can check, rather than guessing.

---

## Output guardrails

- Cite the file (and function/class name where relevant) behind each nontrivial claim, so the user can spot-check without re-running the whole investigation.
- Never invent a field, default, or enum value that isn't confirmed by introspection.
- Treat conflicts between prompts, code, and the old doc as findings to report, not errors to quietly fix — the user may want to fix the code, the prompt, or the doc, and that's their call.
