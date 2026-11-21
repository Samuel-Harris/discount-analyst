set default-list := true

# Start the agent terminal when port 8001 is down.
[working-directory(justfile_directory())]
ensure:
    make ensure-agent-terminal

# Build the sandbox image when it is missing.
[working-directory(justfile_directory())]
build:
    make build-terminal-sandbox

# Rebuild the sandbox image and recreate the terminal.
[working-directory(justfile_directory())]
rebuild:
    make rebuild-agent-terminal

# Rebuild the sandbox image and verify the terminal.
[working-directory(justfile_directory())]
verify:
    make verify-terminal

# Stop the agent terminal.
[working-directory(justfile_directory())]
down:
    docker compose down
