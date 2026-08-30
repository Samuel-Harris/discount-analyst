---
name: implement-linear-ticket
description: Take a Linear ticket to a merge-ready draft GitHub pull request: resolve the issue, branch from origin/$BASE, plan, implement, run thermos, open a draft PR, then babysit until merge-ready. Use when the user asks to implement a Linear ticket, take a ticket to a PR, or run the Linear-to-draft-PR workflow.
---

# Implement Linear Ticket

## Purpose

Use this skill when the user asks you to take a Linear ticket all the way to a merge-ready implementation on a **draft** GitHub pull request. The workflow is intentionally end-to-end: resolve the ticket, create the Linear branch from `origin/$BASE`, plan the implementation, implement it, run `thermos`, refactor from that feedback, then commit, push, and open a draft PR, then load `babysit` until the PR is mergeable, comments are triaged, and CI/CD passes. Leave the GitHub PR as a draft unless the user explicitly asks to mark it ready for review.

## Required Input

The user must provide a Linear issue ID or URL. If an argument was provided (`$ARGUMENTS`), use it as the Linear issue ID. If neither is present, ask for one before doing anything else.

The target base `$BASE` is `main`. Use `$BASE` for branch creation, the thermos merge-base, and the pull request base.

## Hard Safety Rules

- Do not create a worktree.
- Do not use destructive git commands such as `git reset --hard`, `git checkout --`, or branch deletion.
- Start from a clean worktree. If `git status --porcelain` is non-empty before branch creation, stop and ask the user how to handle the existing changes.
- Use the Linear ticket's `gitBranchName` exactly. If Linear does not provide one, stop and ask the user whether to derive a branch name.
- If the local or remote branch already exists, stop and ask before checking it out, rebasing it, pushing to it, or replacing it.
- Never stage files with `git add .`, `git add -A`, or interactive git commands. Stage explicit paths only.
- Never commit likely secrets: `.env`, `.env.*`, credential files, private keys, tokens, passwords, or certificates.
- Never amend commits, force push, or update an existing PR description unless the user explicitly asks.
- Never mark the GitHub PR ready for review, enable auto-merge, or merge it unless the user explicitly asks. This workflow opens drafts by default.
- Before calling any MCP tool, read that tool's descriptor/schema first.
- If a bug or follow-up is discovered outside this ticket's scope, do not implement it on the current branch. Create a Linear ticket with all known detail: what failed, where (links, logs, file paths, PRs), suspected cause, and how to fix. Implement that ticket on a separate branch only after the user asks, or after they invoke this skill on the new issue. Do not mix it into the current PR, stack layer, or unstaged set unless the user explicitly says to include it.

## Workflow

1. **Resolve the Linear ticket**

   Read the Linear MCP descriptors for `get_issue` and `list_comments`, then fetch the ticket and comments:

   - `get_issue` with `id`, `includeRelations: true`, and `includeCustomerNeeds: true`.
   - `list_comments` with `issueId` and a high enough `limit` to capture the ticket discussion.

   Extract the issue key, title, description, acceptance criteria, attachments or linked docs, relationships, customer needs, and `gitBranchName`. Treat the Linear ticket as the source of truth for branch name and scope. Then set `BASE=main`.

2. **Create the branch from `origin/$BASE`**

   Run the state checks in this order:

   ```bash
   git branch --show-current
   git status --porcelain
   git fetch origin "$BASE"
   git show-ref --verify --quiet "refs/heads/$LINEAR_GIT_BRANCH_NAME"
   git ls-remote --exit-code --heads origin "$LINEAR_GIT_BRANCH_NAME"
   ```

   If the worktree is clean and neither branch exists, create the branch:

   ```bash
   git switch -c "$LINEAR_GIT_BRANCH_NAME" "origin/$BASE"
   ```

3. **Plan before editing**

   Gather codebase context before writing code. Use direct reads for known files and a high-reasoning general-purpose subagent for broad exploration. If the ticket is ambiguous after reading Linear and the code, ask the user one targeted question before implementing.

   Write a short but complete implementation plan in chat before editing. The plan must include:

   - The problem being solved and why it matters.
   - Intended behaviour after the change, including user-visible behaviour, system behaviour, edge cases, and failure handling.
   - Non-goals, compatibility expectations, rollout assumptions, and constraints.
   - Chosen design, data flow, invariants, and rejected alternatives when they matter.
   - Blast radius: affected files, APIs, schemas, database objects, generated artefacts, and tests.
   - Concrete execution order.
   - Verification evidence required before PR creation.
   - A final review step that runs `thermos` and refactors from its feedback.

4. **Implement surgically**

   Follow the repository's existing patterns and keep the diff focused on the ticket.

   Add or update tests proportional to the risk. For bug fixes, write or update a focused test that would fail before the fix when practical.

5. **Verify the implementation**

   Run focused tests and checks using the repo's normal commands. At minimum, run the narrowest relevant test or type/lint check that proves the edited behaviour. Record the exact commands and outcomes for the PR body.

6. **Run thermos**

   Load and follow the `thermos` skill, passing `$BASE`, the implementation plan, and verification evidence. That skill owns gathering the merge-base-to-working-tree packet (including untracked files), launching both review subagents in parallel, and synthesising their findings. Do not restate those steps here.

   Apply the synthesised feedback that is correct and in scope. If a recommendation is intentionally rejected, state the reason in chat. Re-run the relevant tests and checks after refactoring. If the review finds serious unresolved issues, stop before committing.

7. **Create the draft PR**

   This step assumes:

   - The Linear ticket is already resolved.
   - The current branch is `$LINEAR_GIT_BRANCH_NAME`, created from `origin/$BASE`.
   - There is no existing PR for the branch.

   Fetch `origin/$BASE` and rebase the current branch onto it. If the rebase has conflicts, abort it, stop, and ask. Then commit the ticket's changes with an explicit path list (never `git add .` or `git add -A`) and a message that names the Linear issue key and why the change exists. Push with `-u` to origin if the branch has no upstream.

   If creating the PR would require renaming the branch, updating an existing PR, amending, or force-pushing, stop and ask instead.

   Create a GitHub draft by default so the work is not reviewable while CI still runs:

   ```bash
   gh pr create --draft --base "$BASE" --title "<issue-key>: <short title>" --body "$(cat <<'EOF'
   ## Summary
   <1-3 bullets of what changed and why>

   ## Test plan
   - [ ] <commands run and expected evidence>
   EOF
   )"
   ```

   Include the Linear issue identifier in the title or body. Put the recorded verification commands and the thermos review outcome in the test plan / summary so reviewers can see what was run and whether in-scope feedback was applied. Omit `--draft` only when the user explicitly asks for a ready-for-review PR. After creation, do not convert the PR to ready.

8. **Babysit the PR until merge-ready**

   Load and follow the `babysit` skill for the newly created PR, passing its number or URL. That skill owns the merge-conflict, comment, and CI loop. Do not declare completion while checks are pending or failing. Do not mark the draft ready, enable auto-merge, or merge. If permissions, an external service, an incompatible conflict, or an out-of-scope failure prevents a merge-ready result, stop and report the exact blocker and failed check or unresolved thread.

## Stop Conditions

Stop and ask the user before continuing if:

- The Linear issue cannot be fetched or is not the intended ticket.
- The ticket lacks a `gitBranchName`.
- The initial worktree is dirty.
- The local or remote branch already exists.
- The implementation requires a product, API, migration, rollout, or compatibility decision not resolved by the ticket.
- Tests or required verification cannot be run.
- The thermos review finds serious issues that cannot be fixed in scope.
- Creating the PR would require updating an existing PR, force pushing, amending, or changing the base branch.
- The babysit phase cannot make the PR merge-ready without weakening checks, making unrelated changes, or resolving an external blocker.

## Verification

Pass when:

- The Linear `gitBranchName` was created from `origin/$BASE` only after the worktree was clean and neither branch existed.
- Focused checks for the ticket's changed behaviour were run and recorded.
- `thermos` ran against the actual ticket edits (merge-base to working tree, including untracked files) and in-scope feedback was applied or explicitly rejected.
- A **draft** PR was created from this branch, unless the user explicitly asked for a ready-for-review PR.

Fail and stop when any stop condition above is hit.

## Final Response

Keep the final response concise. Include the Linear issue key, branch name, final commit SHA, PR URL, whether the PR is still a GitHub draft, tests/checks run, whether thermos feedback was fully addressed, and the final mergeability, review-thread, and CI/CD status. Name any remaining external blocker precisely.
