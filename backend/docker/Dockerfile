# syntax=docker/dockerfile:1

FROM python:3.14-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
ENV UV_LINK_MODE=copy

COPY pyproject.toml uv.lock README.md ./
COPY discount_analyst ./discount_analyst
COPY backend ./backend
COPY scripts ./scripts

RUN uv sync --frozen --group dev

COPY backend/docker/entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/docker-entrypoint.sh"]
