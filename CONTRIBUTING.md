# Contributing to Duo

Thanks for your interest in contributing! This guide covers how to set up
your environment, make changes, and submit them.

## Getting Started

See the [README](README.md) for full setup instructions. In short:

```bash
uv sync                 # install Python dependencies
just generate-proto     # generate gRPC code
just up                 # start services + infra in Docker
```

### Prerequisites

- Python 3.14+
- [uv](https://docs.astral.sh/uv/)
- [just](https://github.com/casey/just)
- [pnpm](https://pnpm.io/)
- Docker + Docker Compose

## Development Workflow

1. Branch off `main`.
2. Make your change.
3. Run `just check` (format + type-check + test) until it passes.
4. Commit using [Conventional Commits](#commit-messages).
5. Open a pull request against `main`.

### Common Commands

All tasks run through `just`:

```bash
just check           # format + type-check + test (run before pushing)
just format          # ruff format + auto-fix
just lint            # ruff lint
just type-check      # basedpyright (strict)
just test            # pytest
just test-cov        # pytest with coverage

just run api         # FastAPI on :8000
just run auth        # Auth gRPC service
just run game        # Game gRPC service
just ui dev          # Vue dev server

just generate-proto  # regenerate gRPC code from .proto files
```

Run a single test path: `pytest services/game/tests/unit/tic_tac_toe/`

## Code Standards

### Python

- Target Python 3.14+.
- `ruff` for formatting and linting: 80-char lines, single quotes.
- `basedpyright` in **strict** mode — no type errors.
- Keep generated gRPC code in `generated/` untouched; regenerate with
  `just generate-proto` instead of editing by hand.

### Frontend

- React 19 + TypeScript + Vite, organized by feature slice
  (`features/{auth,games,profile,shared}`).
- Lint and build via `just ui lint` / `just ui build`.

### Tests

- Written with `pytest`. Each service keeps tests under
  `services/<name>/tests/{unit,integration,e2e}/` — the directory matches
  the marker tier:
  - `tests/unit/` — fast, isolated, no I/O.
  - `tests/integration/` — DB / gRPC / cross-component.
  - `tests/e2e/` — full flow across services.
- Mark tests with the matching marker: `unit`, `integration`, `e2e`,
  or `slow`. Markers are strict (`--strict-markers`) — unknown ones fail.
- Run one tier: `pytest services/game/tests/unit/`.
- Add or update tests for any behavior change.

## Database Migrations

Schema changes use Alembic, scoped per service (`auth`, `game`):

```bash
just make-migrations auth    # autogenerate a revision
just apply-migrations auth   # upgrade to head
just rollback auth           # downgrade to base
```

Commit the generated migration file alongside your code change.

## Commit Messages

This project follows [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>
```

- **type**: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, etc.
- **scope**: the affected area, e.g. `auth`, `game`, `api`, `ui`, `otel`.
- **subject**: imperative mood, lowercase, no trailing period.

Examples:

```
feat(game): add connect four engine
fix(auth): handle expired refresh tokens
refactor(otel): consolidate config in settings
```

## Pull Requests

- Keep PRs focused on a single concern.
- Ensure `just check` passes and CI is green
  (`backend-ci`, `frontend-ci`).
- Describe what changed and why; link related issues.
- Update docs (README, CLAUDE.md) when behavior or commands change.

## Architecture Reference

Three microservices plus a frontend:

```
UI (React 19) -> API (FastAPI :8000) -> Auth (gRPC :50051)
                                     -> Game (gRPC :50052)
```

- `services/api/`   — REST + WebSocket gateway, proxies to gRPC services.
- `services/auth/`  — gRPC UserService (JWT/Ed25519, Argon2, PostgreSQL).
- `services/game/`  — gRPC GameService, game engine abstraction.
- `services/ui/`    — React 19 frontend.
- `common/`         — shared Python utilities.
- `proto/`          — source `.proto` files (output in `generated/`).

New games subclass `GameEngine` in `services/game/engines/base.py`;
`TicTacToe` (`engines/tic_tac_toe.py`) is the reference implementation.
