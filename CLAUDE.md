# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

All tasks use `just` (justfile task runner):

```bash
just check           # format + type-check + test
just format          # ruff format + auto-fix
just lint            # ruff lint
just type-check      # basedpyright strict

just test            # pytest
just test-cov        # pytest with coverage

just run api         # FastAPI on :8000 (uvicorn --reload)
just run auth        # Auth gRPC service
just run game        # Game gRPC service
just ui dev          # React (Vite) dev server; just ui <args> proxies to pnpm

just up              # start all services + infra in Docker
just down            # stop all services + infra

just make-migrations auth   # alembic autogenerate
just apply-migrations auth  # alembic upgrade head
just rollback auth          # alembic downgrade base
just connect-to-db auth     # psql into db

just generate-proto  # regenerate gRPC code from .proto files
just clean           # remove __pycache__
```

Run a single test file: `pytest services/game/tests/unit/tic_tac_toe/`

## Architecture

Three microservices + one frontend:

```
UI (React 19) → API (FastAPI :8000) → Auth (gRPC :50051)
                                 → Game (gRPC :50052)
```

- **`services/api/`** — REST gateway. Exposes `/api/v1/auth/`, `/api/v1/users/`, `/api/v1/games/`, and `/api/v1/ws` (WebSocket). Proxies to Auth and Game via gRPC channels in `main.py`.
- **`services/auth/`** — gRPC UserService. JWT with Ed25519 keys (in `services/auth/keys/`), Argon2 passwords, PostgreSQL on :25432.
- **`services/game/`** — gRPC GameService. Contains game engine abstraction and Tic Tac Toe logic. PostgreSQL on :25433.
- **`services/ui/`** — React 19 + Vite + Zustand + TypeScript frontend. Organized by feature slice (`src/features/{auth,games,profile,shared}`).
- **`common/`** — Shared Python utilities (logging, secrets, tokens, models).
- **`proto/`** — Source `.proto` files. Generated output goes to `generated/`.
- **`monitoring/`** — OpenTelemetry, Prometheus + Grafana config (dashboards, scrape).

## Game Engine Pattern

`services/game/engines/base.py` defines `GameEngine[TState, TMove, TPlayerView]` — a generic abstract base. New games subclass it and implement `get_winner`, `is_draw`, `is_move_possible`, `make_move`, `get_player_view`.

`TicTacToe` in `engines/tic_tac_toe.py` is the reference implementation.

## Code Standards

- Python 3.14+, strict basedpyright, ruff (80 char lines, single quotes)
- Tests live under `services/<name>/tests/{unit,integration,e2e}/`; the directory matches the pytest marker. Place each test in the right tier (`tests/unit/...`, `tests/integration/...`, `tests/e2e/...`)
- Pytest markers: `unit`, `integration`, `e2e`, `slow` (strict — unknown markers fail)
- gRPC generated code lives in `generated/` — do not edit manually, regenerate with `just generate-proto`
- Docker infra per service: `services/<name>/infra.yaml`. Root `compose.yml` includes all infra + monitoring; `services-compose.yml` adds the built service containers (used by `just up`)
