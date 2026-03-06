---
name: swarm
description: Coordinated parallel agents on a shared task list. Analyses the task, decomposes into subtasks, and dispatches agents in batches of up to 4. Use for large-scale implementation, review, or refactoring tasks.
---

# Swarm Skill

Decompose a large task into subtasks and dispatch coordinated agents in parallel batches. Like a dev team tackling multiple files simultaneously.

## Usage

Two entry points:

1. **Direct** — the user describes a task (e.g., "fix all type errors"). The swarm analyses the codebase, plans subtasks, and executes.
2. **From ralplan** — a validated plan file (produced by `ralplan`) is provided. The swarm skips its own analysis and planning, using the plan's tasks, file lists, and dependency graph directly.

## Architecture

```
                  [INPUT]
                     |
        +------------+------------+
        |                         |
  User describes task     Ralplan provides plan
        |                         |
        v                         v
  Phase 1: Analyse          (skip to Phase 2)
  Phase 1.5: Short-circuit
        |                         |
        v                         v
  Phase 2: Plan             Phase 2: Plan from ralplan
        |                         |
        +------------+------------+
                     |
                     v
           [BATCH DISPATCH]
           Group subtasks into batches of <=4
           Dispatch batch via parallel Task calls
                     |
           +---------+---------+---------+
           |         |         |         |
           v         v         v         v
         Agent1   Agent2   Agent3   Agent4
           |         |         |         |
           v         v         v         v
         Result1  Result2  Result3  Result4
                     |
                     v
           [COLLECT & ASSESS]
           - Track completed / failed via TodoWrite
           - Re-dispatch failures if retryable
           - Dispatch next batch
                     |
                     v
           [SUMMARY]
           Report: completed, failed, changes made
```

## Workflow

### Phase 1 — Analyse

> **Skip this phase when a ralplan plan file is provided.** Proceed directly to Phase 2 (ralplan variant).

Use a `explore-medium` subagent to scan the codebase, identify affected files, and break the task into concrete subtasks. Each subtask should target specific files with a clear scope. Use `explore-medium` (not `explore-low`) because decomposition requires cross-module reasoning.

### Phase 1.5 — Short-Circuit Check

If analysis yields fewer than 3 subtasks, skip the swarm machinery — execute them directly (sequentially or with a single parallel dispatch). Full swarm orchestration overhead is not worth it for trivial cases.

### Phase 2 — Plan

**When working from a ralplan:** Read the plan file and extract the task list. Use each task's **Depends on** and **Files** fields to determine batch grouping (independent tasks with no file overlap go in the same batch; dependent tasks go in later batches). Choose agent tiers based on each task's scope — the plan describes _what_, the swarm decides _how_. Then proceed to Phase 3.

**When working from direct input:** For each subtask:

1. Choose the most appropriate `subagent_type` individually — different subtasks can use different agent types and tiers within the same swarm:

   | Agent             | When to use                                                           |
   | ----------------- | --------------------------------------------------------------------- |
   | `executor-low`    | Single-file, mechanical changes (add import, config tweak, rename)    |
   | `executor-medium` | Standard multi-step implementation within a bounded scope             |
   | `executor-high`   | Multi-file refactoring, cross-module changes, complex dependency work |
   | `build-fixer-low` | Single trivial type error or syntax fix                               |
   | `build-fixer`     | Multiple or complex build/type errors                                 |
   | `architect-high`  | Read-only analysis (readonly)                                         |

2. Determine batch grouping: agent count per batch = min(subtask_count_remaining, 4)
3. Create a TodoWrite tracking all subtasks

### Phase 3 — Dispatch

Group subtasks into batches of up to 4. Apply the **file conflict rule**:

> **Subtasks within the same batch must NOT touch overlapping files.** If two subtasks affect the same file, they must be in different batches (sequential, not parallel).

For each agent in the batch, create a Task call with:

- `subagent_type`: the chosen agent type and tier for this subtask (the tier determines the model — no need to override `model`)
- `prompt`: include specific file paths, clear instructions, and "Execute directly. NEVER delegate via Task tool."

Example dispatch (single message with up to 4 parallel Task calls):

```
Task 1: { subagent_type: "build-fixer-low", prompt: "Fix type error in backend/shared/models/user.py: ... Execute directly. NEVER delegate via Task tool." }
Task 2: { subagent_type: "executor-medium", prompt: "Add validation logic in backend/copilot/logic/auth.py: ... Execute directly. NEVER delegate via Task tool." }
Task 3: { subagent_type: "executor-low", prompt: "Add missing import in backend/copilot/api/endpoints/projects.py: ... Execute directly. NEVER delegate via Task tool." }
```

### Phase 4 — Collect

Read results from each agent. For each subtask:

- **Success** → mark completed in TodoWrite
- **Failure** → if retryable (transient error, partial fix), add to next batch; otherwise mark failed

### Phase 5 — Next Batch

If subtasks remain, dispatch the next batch (back to Phase 3). Continue until all subtasks are completed or marked as failed.

### Phase 6 — Summary

Report:

- Total completed
- Total failed (with reasons)
- List of files changed
- Any files needing manual attention

## Key Rules

1. **Max 4 concurrent agents** — Cursor's limit per batch dispatch
2. **File conflict rule** — no two agents in the same batch should touch the same file
3. **Per-subtask agent choice** — different agent types can mix in one swarm
4. **No delegation chains** — every agent prompt must include "Execute directly. NEVER delegate via Task tool."
5. **TodoWrite for progress** — track all subtasks with status updates
6. **Retryable failures** — re-dispatch in the next batch; non-retryable failures are marked and reported

## Examples

### Fix All Type Errors (Direct)

```
→ Phase 1: explore-medium finds 12 type errors across 8 files
→ Phase 2: plan 8 subtasks — 6 trivial (build-fixer-low), 2 complex (build-fixer-medium)
→ Phase 3: dispatch batch 1 (4 agents), batch 2 (4 agents)
→ Phase 6: "8/8 completed, 0 failed, 8 files changed"
```

### Mixed Refactoring (Direct)

```
→ Phase 1: explore-medium identifies 5 subtasks — 2 type fixes, 1 config change, 2 logic implementations
→ Phase 2: plan with build-fixer-low (2), executor-low (1), executor-medium (2)
→ Phase 3: batch 1 dispatches 4 non-overlapping subtasks
→ Phase 5: batch 2 dispatches remaining 1
→ Phase 6: "5/5 completed, 0 failed"
```

### From Ralplan

```
→ Ralplan provides .cursor/plans/add_user_feature.plan.md with 5 tasks:
    Task 1 (model, depends: none), Task 2 (schemas, depends: 1),
    Task 3 (permissions, depends: none), Task 4 (CRUD, depends: 1+2),
    Task 5 (endpoint, depends: 4)
→ Phase 2: read dependency graph — Tasks 1 & 3 are independent, rest sequential
    Batch 1: Task 1 (executor-medium) + Task 3 (executor-low)
    Batch 2: Task 2 (executor-medium)
    Batch 3: Task 4 (executor-medium)
    Batch 4: Task 5 (executor-medium)
→ Phase 3–5: dispatch batches in order
→ Phase 6: "5/5 completed, 0 failed"
```
