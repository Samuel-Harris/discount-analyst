### Installation

FastA2A is available on PyPI as [`fasta2a`](https://pypi.org/project/fasta2a/) so installation is as simple as:

```bash
pip install fasta2a

```

```bash
uv add fasta2a

```

The only dependencies are:

- [starlette](https://www.starlette.io): to expose the A2A server as an [ASGI application](https://asgi.readthedocs.io/en/latest/)
- [pydantic](https://pydantic.dev): to validate the request/response messages
- [opentelemetry-api](https://opentelemetry-python.readthedocs.io/en/latest): to provide tracing capabilities

You can install Pydantic AI with the `a2a` extra to include **FastA2A**:

```bash
pip install 'pydantic-ai-slim[a2a]'

```

```bash
uv add 'pydantic-ai-slim[a2a]'

```
