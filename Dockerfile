# This docker file is intended to be used with docker compose to deploy a production
# instance of a Reflex app.

# =======================================
# Stage 1: init
# =======================================
FROM python:3.14-slim AS builder

# uv installs python packages; reflex uses a bun found on PATH instead of downloading its own.
COPY --from=ghcr.io/astral-sh/uv:0.12 /uv /bin/uv
COPY --from=oven/bun:1 /usr/local/bin/bun /usr/local/bin/bun
ENV UV_COMPILE_BYTECODE=1 UV_NO_CACHE=1 PATH="/app/.venv/bin:$PATH"
ENV UV_NO_DEV=1

WORKDIR /app

# Install dependencies (do this as a separate layer to improve docker build time during
# development).
RUN --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project

# Copy local context to `/app` inside container (see .dockerignore)
COPY . .
RUN mkdir -p /app/data /app/uploaded_files

# Install application in venv
RUN uv sync --locked

# Compile the app and build the static frontend. The cache mount keeps bun's
# package cache between builds so unchanged dependencies are not downloaded again.
RUN --mount=type=cache,target=/root/.bun/install/cache \
    uv run reflex export --frontend-only --no-zip


# =======================================
# Stage 2: copy artifacts into slim image
# =======================================
FROM python:3.14-slim

ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1

WORKDIR /app
# The app user needs to own /app itself so reflex can create .states there.
RUN adduser --disabled-password --gecos "" --home /app reflex && chown reflex /app
COPY --chown=reflex --from=builder /app/.venv .venv
COPY --chown=reflex --from=builder /app/.web/backend .web/backend
COPY --chown=reflex --from=builder /app/.web/build/client .web/build/client
COPY --chown=reflex . .
USER reflex

RUN mkdir -p data uploaded_files

# Always apply migrations before starting the backend.
CMD test -d alembic && reflex db migrate; \
    exec reflex run --env prod --backend-only

# Apply migrations before starting the backend; a failed migration stops the container.
CMD if [ -d alembic ]; then reflex db migrate; fi && \
    exec reflex run --env prod --backend-only
