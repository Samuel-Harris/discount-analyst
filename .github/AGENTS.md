<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-02-23 | Updated: 2026-02-23 -->

# .github

## Purpose

The `.github/` directory contains GitHub-specific configuration files, automation workflows, and community health files. It serves as the central hub for the project's CI/CD pipeline, custom automation logic (GitHub Actions), and standardized templates for contributions like pull requests.

## Key Files

| File | Description |
| --------- | ---------------------------- |
| `pull_request_template.md` | Provides a standardized checklist for contributors when opening new pull requests. |

## Subdirectories

| Directory | Purpose |
| --------- | ----------------------------------------- |
| `workflows/` | Contains GitHub Actions workflow definitions (e.g., CI, deployment). |
| `actions/` | Contains custom, reusable GitHub Actions developed specifically for this project. |

## For AI Agents

### Working In This Directory

- **YAML Validation**: Always ensure correct indentation and syntax when modifying workflow files in `workflows/`.
- **Reusable Logic**: Prefer extracting repeated setup or build steps into custom actions within `actions/` to keep workflows clean.
- **Versioning**: Use specific versions for external actions (e.g., `actions/checkout@v4`) to ensure build stability.

### Testing Requirements

- **CI Verification**: Changes to workflows or actions must be verified by pushing to a branch and monitoring the GitHub Actions tab for success/failure.
- **Local Testing**: If the environment supports it, use tools like `act` to test workflows locally before pushing.

### Common Patterns

- **Composite Actions**: Uses composite actions (found in `actions/`) to standardize environment setup (Python version, Poetry installation, dependency caching) across different jobs.
- **Triggering**: Workflows are typically triggered on `push` and `pull_request` events to the `main` branch.

## Dependencies

### Internal

- **Root Project**: Workflows depend on `pyproject.toml` and `poetry.lock` for environment setup and dependency management.
- **Core Source**: CI workflows execute tests and linters against the code in `discount_analyst/` and `scripts/`.

### External

- **actions/checkout**: Standard GitHub action for checking out the repository code.
- **actions/setup-python**: Official GitHub action for setting up the Python environment.
- **Poetry**: Used within workflows for dependency installation and test execution.

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
