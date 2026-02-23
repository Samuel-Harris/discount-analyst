---
name: generate-agent-docs
description: Initialise comprehensive hierarchical AGENTS.md documentation across the entire codebase.
disable-model-invocation: true
---

# Generate Agent Documentation

Use the `agents-md` skill to create or update AGENTS.md documentation.

**Scope:**

- If the user has already specified a directory or path (e.g. "just `src/`", "only this folder", "in `docs/api`"), apply the skill to **that scope only**.
- Otherwise apply the skill to the **entire codebase**.

Follow the skill's workflow for the chosen scope (single-directory steps when scoped, full level-by-level workflow when repo-wide).
