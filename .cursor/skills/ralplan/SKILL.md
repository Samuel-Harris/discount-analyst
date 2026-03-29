---
name: ralplan
description: Iterative planning consensus loop. Orchestrates Planner, Architect, and Critic agents in rounds until the plan is approved or max iterations reached. Use for complex tasks that need a validated plan before implementation.
---

# Ralplan — Iterative Planning Consensus

Orchestrate **Planner**, **Architect**, and **Critic** agents in iterative rounds until the Critic approves the plan or 5 iterations are exhausted.

## When to Use

Large, ambiguous, or architecturally significant tasks that need a validated work plan before implementation begins.

## Agent Roles

| Agent     | `subagent_type` | Role                                                                                     |
| --------- | --------------- | ---------------------------------------------------------------------------------------- |
| Planner   | `planner`       | Creates and refines the work plan (writes to the plan path supplied by the orchestrator) |
| Architect | `architect`     | Answers architectural questions, validates design (readonly)                             |
| Critic    | `critic`        | Reviews the plan; issues OKAY or REJECT verdict (readonly)                               |

## Loop

```
Planner creates plan
  → (if open questions) Architect answers
  → (if multi-task plan) Architect validates dependency graph
  → Critic reviews           ← MANDATORY, never skip
  → OKAY → Done
  → REJECT → feed criticism to Planner, repeat
```

## Plan Structure

The Planner decides how to structure the plan, but must annotate **task dependencies** when the plan contains multiple tasks. This lets downstream execution determine ordering and parallelism.

### Dependency Annotations

For each task in a multi-task plan, the Planner should note:

- **Depends on**: which prior tasks (if any) must complete first, or "none" if independent
- **Files**: the file paths the task reads or writes

These are lightweight annotations — the Planner should **not** prescribe batch grouping, agent tiers, or execution strategy. Those are execution concerns handled by whoever runs the plan.

Example:

```markdown
### Task 1: Add User model

- **Files**: `backend/shared/models/user.py`
- **Depends on**: none

### Task 2: Add User schemas

- **Files**: `backend/shared/schemas/user.py`
- **Depends on**: Task 1

### Task 3: Add permission constants

- **Files**: `backend/shared/constants/permissions.py`
- **Depends on**: none
```

Tasks 1 and 3 are independent (an executor could parallelise them); Task 2 depends on Task 1 (must be sequential). The plan states the _what_ — execution decides the _how_.

## Execution Protocol

### 0. Resolve Ambiguities (if needed)

Before planning, assess whether the developer's intention is clear enough to produce a useful plan.

If the task description is vague, contradictory, missing acceptance criteria, or leaves key architectural decisions open, run the **deep-interview** skill first.

The deep-interview skill runs a Socratic Q&A loop that scores ambiguity across weighted dimensions and refuses to exit until ambiguity drops below 20%. When it completes, it writes a crystal-clear spec to `.cursor/artefacts/interviews/`. Use that spec as the task description for the planning loop.

**Skip this step** if the request already includes specific file paths and acceptance criteria, the user has an existing plan or interview file, or the user says "just plan it" / "don't interview me".

### 1. Initialise

- Parse the user's task description
- Create the plan file:
  - **If in plan mode** (a `<system_reminder>` block in your context says "Plan mode is active") → call the `CreatePlan` tool with the feature name and a one-line overview. Capture the returned file path as `plan_path`.
  - **Otherwise** → run `date '+%Y-%m-%d_%H-%M-%S'` in the terminal, create `.cursor/plans/YYYY-MM-DD_HH-MM-SS_<feature-name>.md`, and set `plan_path` to that path.
- Create a TodoWrite to track iteration progress

### 2. Invoke Planner

Dispatch via Task with `subagent_type: "cursor-planner"`. The planner automatically skips its interview phase when context is pre-provided by an orchestrator.

The prompt must:

- Provide the full task description and any prior Critic feedback (if iterating)
- State that this is a ralplan invocation (triggers the planner's direct planning mode)
- Supply the plan path: "A plan file has been created at `{plan_path}`. Write your plan content there; do not create a new file."
- Instruct the Planner to annotate each task with **Files** and **Depends on** fields when the plan has multiple tasks
- End with: "Execute directly. NEVER delegate via Task tool. Return the plan file path."

> **Note**: the Planner subagent will not be in plan mode (subagents do not inherit plan mode). It writes to `plan_path` because the orchestrator supplies it — not because of any plan-mode detection.

### 3. Architect Consultation

Invoke in either of these cases:

1. **Open questions** — the Planner raised architectural questions it cannot answer alone
2. **Dependency validation** — the plan has multiple tasks and the Architect should verify the dependency graph is correct (no missing dependencies, no false sequencing that blocks parallelism)

Dispatch via Task with `subagent_type: "cursor-architect-high"` (readonly). The architect gathers context via parallel tool calls, performs deep analysis, and returns prioritised recommendations with `file:line` citations.

For dependency validation, ask the Architect to check:

- Whether tasks marked independent truly have no shared state or import dependencies
- Whether any sequential dependency could be relaxed (enabling more parallelism)
- Whether any task's file list is incomplete (missing files that would create hidden conflicts)

Feed answers back to the Planner in the next iteration.

### 4. Critic Review — MANDATORY

**Always invoke after the Planner finishes.** No plan is approved without a Critic verdict.

Dispatch via Task with `subagent_type: "cursor-critic"` (readonly). Provide the plan file path. The Critic evaluates four criteria (clarity, verifiability, context completeness, big picture), simulates implementation of 2–3 tasks, and returns an OKAY or REJECT verdict with specific improvements.

For multi-task plans, the Critic should additionally verify that dependency annotations are accurate and file lists are complete.

### 5. Handle Verdict

| Verdict                    | Action                                                                  |
| -------------------------- | ----------------------------------------------------------------------- |
| **OKAY**                   | Plan approved. Report to the user and offer to begin execution.         |
| **REJECT** (iteration < 5) | Feed Critic feedback to the Planner. Increment iteration. Go to step 2. |
| **REJECT** (iteration = 5) | Force-approve with warning. Recommend manual review before execution.   |

Update TodoWrite after each verdict.

## Handoff to Swarm

Once approved, a multi-task plan with dependency annotations can be handed to `cursor-swarm` for execution. The swarm reads the dependency graph and file lists to determine batch grouping and agent selection — it skips its own analysis phase when given a ralplan. See the swarm skill for details.

## Rules

1. **Ambiguity first** — if intention is unclear, run deep-interview before planning
2. **Critic is mandatory** — no plan is approved without a Critic verdict
3. **Planner owns the plan file** — only the Planner writes to it
4. **Architect advises only** — reads and recommends, never modifies
5. **Feedback is specific** — every rejection includes actionable improvements
6. **Max 5 iterations** — hard safety limit
7. **Sequential dispatch** — Planner → (Architect) → Critic, one agent at a time
8. **No delegation chains** — every agent prompt ends with "Execute directly. NEVER delegate via Task tool."
9. **Plan describes what, not how** — dependency annotations and file lists inform execution but the plan must not prescribe batch grouping, agent tiers, or execution strategy
