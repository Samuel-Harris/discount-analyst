# Private default: `just check` runs these recipes in this order.
[default]
[private]
[working-directory(justfile_directory())]
all: pytest pyright lint-imports tach frontend-lint frontend-test frontend-build

# Run the Python test suite.
[working-directory(justfile_directory())]
pytest:
    uv run pytest

# Type-check the Python sources.
[working-directory(justfile_directory())]
pyright:
    uv run pyright

# Check import boundaries.
[working-directory(justfile_directory())]
lint-imports:
    uv run lint-imports

# Check declared third-party dependencies.
[working-directory(justfile_directory())]
tach:
    uv run tach check-external

# Lint the frontend.
[working-directory(justfile_directory())]
frontend-lint:
    pnpm --dir frontend lint

# Test the frontend.
[working-directory(justfile_directory())]
frontend-test:
    pnpm --dir frontend test

# Build the frontend.
[working-directory(justfile_directory())]
frontend-build:
    pnpm --dir frontend run build
