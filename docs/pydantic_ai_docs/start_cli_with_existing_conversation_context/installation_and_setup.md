## Installation and Setup

Clone your fork and cd into the repo directory

```bash
git clone git@github.com:<your username>/pydantic-ai.git
cd pydantic-ai

```

Install `uv` (version 0.4.30 or later), `pre-commit` and `deno`:

- [`uv` install docs](https://docs.astral.sh/uv/getting-started/installation/)
- [`pre-commit` install docs](https://pre-commit.com/#install)
- [`deno` install docs](https://docs.deno.com/runtime/getting_started/installation/)

To install `pre-commit` you can run the following command:

```bash
uv tool install pre-commit

```

For `deno`, you can run the following, or check [their documentation](https://docs.deno.com/runtime/getting_started/installation/) for alternative installation methods:

```bash
curl -fsSL https://deno.land/install.sh | sh

```

Install `pydantic-ai`, all dependencies and pre-commit hooks

```bash
make install

```
