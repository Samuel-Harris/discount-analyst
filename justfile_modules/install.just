# Private default: `just install` runs uv, then pnpm.
[default]
[private]
[working-directory(justfile_directory())]
all: uv pnpm

# Install the Python packages from uv.lock.
[working-directory(justfile_directory())]
uv:
    uv sync

# Install the frontend packages from the lockfile.
[working-directory(justfile_directory())]
pnpm:
    pnpm --dir frontend install --frozen-lockfile
