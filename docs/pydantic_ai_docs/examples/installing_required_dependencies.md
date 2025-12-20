### Installing required dependencies

Either way you'll need to install extra dependencies to run some examples, you just need to install the `examples` optional dependency group.

If you've installed `pydantic-ai` via pip/uv, you can install the extra dependencies with:

```bash
pip install "pydantic-ai[examples]"

```

```bash
uv add "pydantic-ai[examples]"

```

If you clone the repo, you should instead use `uv sync --extra examples` to install extra dependencies.
