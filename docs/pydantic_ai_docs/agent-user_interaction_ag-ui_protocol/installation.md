## Installation

The only dependencies are:

- [ag-ui-protocol](https://docs.ag-ui.com/introduction): to provide the AG-UI types and encoder.
- [starlette](https://www.starlette.io): to handle [ASGI](https://asgi.readthedocs.io/en/latest/) requests from a framework like FastAPI.

You can install Pydantic AI with the `ag-ui` extra to ensure you have all the required AG-UI dependencies:

```bash
pip install 'pydantic-ai-slim[ag-ui]'

```

```bash
uv add 'pydantic-ai-slim[ag-ui]'

```

To run the examples you'll also need:

- [uvicorn](https://www.uvicorn.org/) or another ASGI compatible server

```bash
pip install uvicorn

```

```bash
uv add uvicorn

```
