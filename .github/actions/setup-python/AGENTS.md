<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-02-23 | Updated: 2026-02-23 -->

# setup-python

## Purpose

The `setup-python` directory contains a reusable GitHub composite action designed to standardize the environment setup for the Discount Analyst project. It ensures that the correct version of Python is installed and that all project dependencies are consistently managed via uv.

## Key Files

| File | Description |
| --------- | ---------------------------- |
| `action.yml` | Metadata and implementation for the "Setup Python and Dependencies" composite action. |

## Subdirectories

| Directory | Purpose |
| --------- | ----------------------------------------- |
| (None) | This directory contains a single composite action. |

## For AI Agents

### Working In This Directory

- **Python Version**: This action specifically targets Python 3.14. Any changes to the project's Python version requirements should be reflected here.
- **Dependency Management**: It uses `uv` for dependency installation. Ensure `uv sync` remains the standard for setting up the development environment.
- **Composite Action**: Modifications should adhere to the GitHub Actions `composite` run type syntax.

### Testing Requirements

- **CI Verification**: Any changes to `action.yml` should be verified by running a GitHub Actions workflow that references this action (e.g., `.github/workflows/ci.yml`).
- **Syntax**: Ensure the YAML structure is valid and all steps use the `bash` shell where required.

### Common Patterns

- **Standardized Setup**: This action is used across different workflows (like CI, linting, etc.) to ensure environment parity.

## Dependencies

### Internal

- **Parent Directory**: Inherits project-wide automation standards from `.github/actions/AGENTS.md`.

### External

- **actions/setup-python@v5**: Used to install the Python runtime.
- **uv**: Used for installing project dependencies.

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
