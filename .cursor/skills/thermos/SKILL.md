---
name: thermos
description: "Launch both thermo-nuclear review subagents in parallel, then synthesise their findings. Use for thermos, double thermo review, or combined bug/security and code-quality branch audits."
disable-model-invocation: true
---

# Thermos

Run the two thermo review passes as async background subagents in parallel, then synthesise their results.

This skill owns the review packet, the parallel launch, and the synthesis. Callers pass `$BASE` (and optionally a pre-built packet, the implementation plan, and verification evidence). Do not re-gather in the caller or in the review subagents.

## Packet

If the caller already passed a packet, use it. Otherwise gather the actual edits from the merge-base with `$BASE` to the working tree, including untracked files.

`$BASE` is the comparison base (branch name, without `origin/`). If the caller does not pass it, take it from the user request or the PR base. Do not default to `main` when a different base is in play. Do not use the current branch's git upstream (`@{upstream}`): on a pushed feature branch that is `origin/<same-branch>`, so `merge-base` collapses to `HEAD` and the packet misses committed work. If `$BASE` is still unknown, ask.

Do not use two-dot `git diff origin/$BASE` (that reverse-diffs later commits on `$BASE`) and do not use three-dot `origin/$BASE...HEAD` alone (that misses uncommitted work).

```bash
git fetch origin "$BASE"
MERGE_BASE=$(git merge-base "origin/$BASE" HEAD)
git status --porcelain
git diff --name-only -M "$MERGE_BASE"
git ls-files --others --exclude-standard
git diff --numstat -M "$MERGE_BASE"
git diff "$MERGE_BASE"
```

Include contents of untracked files in the packet.

## Workflow

1. Determine the review scope from the user request, PR, current branch, or relevant changed files.
2. Gather the packet above unless the caller already passed one.
3. Launch both subagents in the same message with `run_in_background: true`:
   - `subagent_type: "thermo-nuclear-review-subagent"` for bugs, breakages, security, devex regressions, feature-flag leaks, and other branch-audit risks.
   - `subagent_type: "thermo-nuclear-code-quality-review-subagent"` for maintainability, structure, file-size growth, spaghetti, abstractions, and codebase-health risks.
4. Pass each subagent the same scoped packet (and any plan or verification evidence the caller supplied) and ask it to return prioritised findings with file references and evidence.
5. After both finish, synthesise the results with findings first, deduplicated across reviewers. Weight overlapping findings more heavily, resolve disagreements with your own judgement, and keep summaries brief.

If individual background summaries are already visible to the user, do not restate them wholesale. Surface the unified verdict, the highest-signal findings, and any remaining uncertainty.
