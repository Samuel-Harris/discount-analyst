## Install

As Outlines is a library allowing you to run models from various different providers, it does not include the necessary dependencies for any provider by default. As a result, to use the OutlinesModel, you must install `pydantic-ai-slim` with an optional group composed of outlines, a dash, and the name of the specific model provider you would use through Outlines. For instance:

```bash
pip install "pydantic-ai-slim[outlines-transformers]"

```

```bash
uv add "pydantic-ai-slim[outlines-transformers]"

```

Or

```bash
pip install "pydantic-ai-slim[outlines-mlxlm]"

```

```bash
uv add "pydantic-ai-slim[outlines-mlxlm]"

```

There are 5 optional groups for the 5 model providers supported through Outlines:

- `outlines-transformers`
- `outlines-llamacpp`
- `outlines-mlxlm`
- `outlines-sglang`
- `outlines-vllm-offline`
