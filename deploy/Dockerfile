FROM python:3.14-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.11.14 /uv /uvx /bin/

RUN apt-get update && \
    apt-get install -y --no-install-recommends libprotobuf-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-cache --no-group dev --group grpc

COPY proto/ ./proto/
COPY services/ ./services/
COPY common/ ./common/

ENV PATH="/app/.venv/bin:$PATH"

RUN mkdir -p generated && \
    cp proto/*.proto generated/ && \
    python -m grpc_tools.protoc -I . --python_out=. --grpc_python_out=. generated/*.proto && \
    rm generated/*.proto

RUN uv sync --frozen --no-cache --no-group dev --group production --no-group grpc --compile-bytecode


FROM python:3.14-slim

RUN groupadd -r app && useradd -r -g app app

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONFAULTHANDLER=1
ENV PATH="/app/.venv/bin:$PATH"

COPY --from=builder --chown=app:app /app/.venv /app/.venv
COPY --from=builder --chown=app:app /app/services /app/services
COPY --from=builder --chown=app:app /app/common /app/common
COPY --from=builder --chown=app:app /app/generated /app/generated

USER app
