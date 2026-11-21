set default-list := true

# Install Python and frontend dependencies.
mod install 'justfile_modules/install.just'

# Run the dashboard and the agent terminal.
mod run 'justfile_modules/run.just'

# Run tests and static checks.
mod check 'justfile_modules/check.just'
