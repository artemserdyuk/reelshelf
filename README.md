# ReelShelf

A REST API for personal movie watchlists.

## Current Status

The project foundation is implemented:
- FastAPI application factory.
- Liveness endpoint.
- Automated test.
- Ruff, strict mypy, and an 80% coverage gate.

Authentication and watchlist endpoints are planned.
See `docs/api.md` for the target API contract.

## Requirements

- Python 3.14, or permission for uv to install it.
- uv.
- Make, if using the convenience commands.

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