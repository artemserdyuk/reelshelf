# ReelShelf

A REST API for personal movie watchlists.

## Current Status

The following components are implemented:
- FastAPI application factory.
- Validated configuration loaded from environment variables and `.env`.
- Required JWT secret with no default value.
- Liveness endpoint.
- Consistent JSON error responses.
- Isolated configuration and API error tests.
- Ruff, strict mypy, and an 80% coverage gate.

- Domain entities for users, watchlist entries, and refresh sessions.
- Repository protocols and in-memory implementations.
- Owner-scoped entry operations, filtering, and pagination.
- Per-application storage isolation.
- Atomic refresh-session consumption within one event loop.

Authentication and watchlist endpoints are planned.
See `docs/api.md` for the target API contract.

## Storage Limitations

Data is stored in memory and is lost when the application restarts.
The application must run as a single process.

Each application instance owns separate repositories.
Multiple worker processes would not share their data.

Atomic refresh-session consumption is a storage primitive.
The complete refresh rotation workflow is implemented in the
authentication stage.

Goal 8 replaces in-memory storage with PostgreSQL.

## Requirements

- Python 3.14, or permission for uv to install it.
- uv.
- Make, if using the convenience commands.

## Local Configuration

Run all commands from the repository root.

Before the first application start:
1. Copy `.env.example` to `.env`.
2. Generate a local secret:

   ```bash
   uv run python -c "import secrets; print(secrets.token_urlsafe(48))"
   ```

3. Set `REELSHELF_JWT_SECRET` in `.env` to the generated value.

Do not commit `.env`.
Environment variables override values from `.env`.
The application refuses to start with invalid configuration.

Tests use isolated settings and do not require a local `.env`.

## Run

From the repository root:

```bash
make run
```

Alternatively:

```bash
uv run --locked uvicorn reelshelf.main:create_app --factory --reload
```

uv creates the local environment and installs locked dependencies
when necessary.

Open:
- API documentation: http://127.0.0.1:8000/docs
- Liveness: http://127.0.0.1:8000/health/live

## Verify

```bash
make check
```

Or run the checks individually:

```bash
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy src tests
uv run --locked pytest --cov=reelshelf --cov-report=term-missing --cov-fail-under=80
```

## Format

```bash
make format
```

## Design

- `docs/domain.md`
- `docs/api.md`
- `docs/architecture.md`

## Roadmap

Goal 7 delivers authentication and private watchlists using in-memory
repositories.

Goal 8 adds PostgreSQL, async SQLAlchemy, Alembic, Docker Compose,
CI, structured logging, and database readiness checks.