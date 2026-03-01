# Migration Examples

Detailed examples for migrating artefacts to skills and writing recommendations.

## Migrating Apply-Intelligently Rules to Skills (Optional)

Rules with "Apply Intelligently" configuration (has `description`, no `globs`) can optionally be migrated to skills. This is beneficial when:

- The rule contains multi-step procedural instructions
- The rule would benefit from `references/` subdirectory organisation
- The rule is >200 lines and could use progressive disclosure

**Note:** Cursor includes a built-in `/migrate-to-skills` command that can do this automatically.

Manual migration:

**Before** (`.cursor/rules/my-rule.mdc`):

```yaml
---
description: What this rule does
globs:
alwaysApply: false
---
# Title
Body content...
```

**After** (`.cursor/skills/my-rule/SKILL.md`):

```yaml
---
name: my-rule
description: What this rule does
---
# Title
Body content...
```

The skill format provides the same agent-discovery via description, but with better organisation (reference docs in subdirectories) and clearer intent.

---

## Migrating Commands to Skills (Optional)

Commands still work, but skills with `disable-model-invocation: true` are the newer alternative. Cursor's built-in `/migrate-to-skills` command can do this automatically.

Manual migration:

**Before** (`.cursor/commands/commit.md`):

```markdown
# Commit current work

Instructions here...
```

**After** (`.cursor/skills/commit/SKILL.md`):

```yaml
---
name: commit
description: Commit current work with standardized message format
disable-model-invocation: true
---
# Commit current work
Instructions here...
```

The `disable-model-invocation: true` flag prevents the model from automatically invoking the skill — it will only be triggered when the user explicitly types `/commit`.

---

## Example Recommendations

### [P0] Fix missing skill frontmatter

> `.cursor/skills/devtools-cli/SKILL.md` is missing its frontmatter block. Without `name` and `description`, the agent cannot discover this skill.
>
> **Add frontmatter** to the beginning of the file:
>
> ```yaml
> ---
> name: devtools-cli
> description: CLI command reference for development tasks. Use when the user asks to start services, run tests, manage worktrees, or reset the database.
> ---
> # Devtools CLI
> [existing content...]
> ```
>
> **Why:** Skills without `description` in frontmatter are invisible to the agent's skill discovery. The agent will never proactively use this skill, defeating its purpose.

### [P0] Extract area-specific content from root AGENTS.md

> The root AGENTS.md contains 45 lines of Alembic migration conventions (lines 87–131). This loads on every request but is only relevant when working with migration files.
>
> **Create** `.cursor/rules/alembic-migrations.mdc`:
>
> ```yaml
> ---
> description: Alembic migration conventions and safety checks
> globs: backend/alembic/**
> alwaysApply: false
> ---
> [extracted migration content]
> ```
>
> **Remove** lines 87–131 from `AGENTS.md` and replace with a one-line pointer: `| backend/alembic/ | Database migrations (see alembic-migrations rule) |`
>
> **Why:** Reduces always-on context by ~45 lines while preserving the guidance where it's needed.

### [P2] Consider migrating apply-intelligently rule to skill

> `.cursor/rules/code-review.mdc` uses "Apply Intelligently" (has `description`, no `globs`). This rule contains 150+ lines of procedural checklists that would benefit from skill organisation.
>
> **Option A:** Use Cursor's built-in migration: Type `/migrate-to-skills` in Agent chat.
>
> **Option B:** Manual migration — **Create** `.cursor/skills/code-review/SKILL.md`:
>
> ```yaml
> ---
> name: code-review
> description: Code review checklist and best practices. Use when reviewing PRs or performing code review.
> ---
> [original rule body content, preserved exactly]
> ```
>
> **Delete** `.cursor/rules/code-review.mdc`
>
> **Why:** Skills provide better organisation for procedural content via `references/` subdirectories and progressive disclosure. Apply-intelligently rules still work but lack this structure.

### [P2] Consider migrating slash command to skill

> `.cursor/commands/deploy.md` is a slash command that could be converted to a skill.
>
> **Option A:** Use Cursor's built-in migration: Type `/migrate-to-skills` in Agent chat.
>
> **Option B:** Manual migration — **Create** `.cursor/skills/deploy/SKILL.md`:
>
> ```yaml
> ---
> name: deploy
> description: Deploy the application to staging or production environments
> disable-model-invocation: true
> ---
> [original command content, preserved exactly]
> ```
>
> **Delete** `.cursor/commands/deploy.md`
>
> **Why:** Skills with `disable-model-invocation: true` provide the same user-invoked behaviour (`/deploy`) with better organisation via `references/` subdirectories. Commands still work but lack this structure.

### [P1] Add indexing exclusions for non-code content

> The `data/legal-documents/` directory contains 2,847 markdown files (MPEP chapters, case law) totalling 45MB. These pollute the semantic index and dominate search results.
>
> **Add to** `.cursorindexingignore`:
>
> ```
> # Legal reference documents (not source code)
> data/legal-documents/
> ```
>
> **Why:** Removes non-code content from the index, improving search relevance without making the files inaccessible (they can still be manually added via `@file`).

### [P2] Add environment activation hook

> The project uses a conda environment (`.conda/` directory exists) but has no hook to activate it before shell commands. This causes environment mismatch errors.
>
> **Create** `.cursor/hooks.json`:
>
> ```json
> {
>   "version": 1,
>   "hooks": {
>     "sessionStart": [
>       {
>         "command": ".cursor/hooks/session-init.sh"
>       }
>     ]
>   }
> }
> ```
>
> **Create** `.cursor/hooks/session-init.sh`:
>
> ```bash
> #!/bin/bash
> # Read JSON input from stdin
> cat > /dev/null
> # Output env vars for the session
> echo '{"env": {"CONDA_DEFAULT_ENV": "myenv"}}'
> ```
>
> **Why:** Ensures shell commands run in the correct environment, preventing "module not found" errors.
