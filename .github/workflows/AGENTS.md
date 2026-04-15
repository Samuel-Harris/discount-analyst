<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-02-23 | Updated: 2026-04-15 -->

# workflows

## Purpose

The `workflows/` directory contains GitHub Actions workflow definitions that automate the project's Continuous Integration (CI) and potentially Continuous Deployment (CD) processes. These workflows ensure that every change pushed to the repository meets quality standards by running linters, tests, and security checks automatically.

## Key Files

| File     | Description                                                                                                                                                                                                                                                         |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ci.yml` | The primary Continuous Integration workflow: pre-commit, pytest (with coverage for `discount_analyst/` and `backend/`), pyright, a Node-only frontend build and Vitest job, and an OpenAPI/Orval drift check that rebuilds the dashboard client after regeneration. |

## Subdirectories

None.

## For AI Agents

### Working In This Directory

- **YAML Validation**: Always ensure correct indentation and valid YAML syntax when modifying workflow files.
- **Action Selection**: Use stable versions of actions (e.g., `actions/checkout@v4`).
- **Environment Setup**: Use the project's internal composite action `./.github/actions/setup-python` to ensure consistent Python and uv environments across all jobs.

### Testing Requirements

- **Live Verification**: Changes to workflows must be tested by pushing to a branch and verifying the execution in the GitHub Actions tab.
- **Job Dependencies**: Ensure that jobs are correctly ordered and that dependencies (like environment setup) are satisfied.

### Common Patterns

- **Multi-Job Workflows**: Workflows are divided into logical jobs (e.g., `pre-commit`, `pytest`, `pyrefly`) to provide clear feedback on specific failures.
- **uv Execution**: Use `uv run` for all command executions to ensure the correct virtual environment is used.

## Dependencies

### Internal

- **.github/actions/setup-python/**: A local composite action used to standardize the setup of Python, uv, and dependencies.
- **pyproject.toml / uv.lock**: Define the environment and dependencies used during CI runs.

### External

- **GitHub Actions**: The underlying automation platform.
- **pre-commit**: Used for automated linting and formatting checks.
- **pytest**: The primary testing framework.
- **pyright**: Used for automated code analysis and review.

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
