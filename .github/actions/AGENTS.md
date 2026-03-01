<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-02-23 | Updated: 2026-02-23 -->

# actions

## Purpose

The `.github/actions/` directory contains custom, reusable GitHub Actions developed specifically for this project. These actions encapsulate complex or repeated setup and build logic to keep main workflow files clean and maintainable.

## Key Files

| File | Description |
| --------- | ---------------------------- |
| (None) | This directory primarily serves as a container for custom action subdirectories. |

## Subdirectories

| Directory | Purpose |
| --------- | ----------------------------------------- |
| `setup-python/` | Standardizes the setup of Python 3.14 and uv dependencies (see `setup-python/AGENTS.md`). |

## For AI Agents

### Working In This Directory

- **Composite Actions**: New reusable logic should be implemented as composite actions (`action.yml`) within a dedicated subdirectory.
- **Encapsulation**: Ensure actions are self-contained and take necessary inputs to minimize hardcoded dependencies on workflow context.

### Testing Requirements

- **CI Verification**: Verify custom actions by referencing them in a test workflow and pushing to a branch.
- **Syntax Check**: Ensure `action.yml` files follow the GitHub Actions metadata syntax.

### Common Patterns

- **Using Composite**: All custom actions in this project use the `composite` runner type to combine multiple shell steps and external actions.

## Dependencies

### Internal

- **Parent Directory**: Inherits project-wide automation standards from `.github/AGENTS.md`.

### External

- **GitHub Actions Runner**: The environment where these actions execute.
- **uv**: Frequently used within these actions for dependency management.

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
