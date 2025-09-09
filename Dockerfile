# This docker file is intended to be used with docker compose to deploy a production
# instance of a Reflex app.

# =======================================
# Stage 1: init
# =======================================
FROM ghcr.io/astral-sh/uv:0.7.8-python3.13-bookworm AS init

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1
ENV UV_NO_CACHE=1
ENV UV_NO_DEV=1

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

# Deploy templates and prepare app
RUN uv run reflex init

# Export static copy of frontend to /app/.web/build/client
RUN uv run reflex export --frontend-only --no-zip

# Copy static files out of /app to save space in backend image
RUN mv .web/build/client /tmp/client
RUN rm -rf .web && mkdir -p .web/build
RUN mv /tmp/client .web/build/client

# =======================================
# Stage 2: copy artifacts into slim image
# =======================================
FROM python:3.13-slim

# Install libpq-dev for psycopg (skip if not using postgres).
RUN apt-get update -y && apt-get install -y libpq-dev && rm -rf /var/lib/apt/lists/*

WORKDIR /app
RUN adduser --disabled-password --home /app reflex
COPY --chown=reflex --from=init /app /app

USER reflex
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1

# Needed until Reflex properly passes SIGTERM on backend.
STOPSIGNAL SIGKILL

# Always apply migrations before starting the backend.
CMD test -d alembic && reflex db migrate; \
    exec reflex run --env prod --backend-only
