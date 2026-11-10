# ReelShelf

A REST API for personal movie watchlists.

## Current Status

The following features are implemented:

- FastAPI application factory and validated environment configuration.
- Required JWT secret with no default value.
- Liveness endpoint and consistent JSON error responses.
- User registration with username normalization and Argon2 password hashing.
- Login with JWT access and refresh tokens.
- Refresh-token rotation, replay detection, and logout.
- Current-user endpoint.
- Private watchlist creation, listing, retrieval, updates, and deletion.
- Status filtering and offset pagination.
- Owner-scoped access to watchlist entries.
- In-memory repositories isolated per application instance.
- Automated tests, including a complete user journey.
- Ruff, strict mypy, and an 80% coverage gate.
- Owner-scoped watchlist statistics, including average rating.
- Mark-watched endpoint with idempotent behaviour and rating preservation.
- Clear-rating endpoint with idempotent behaviour and status preservation.

Summary, mark-watched, and clear-rating endpoints remain planned extensions.
See `docs/api.md` for the implemented API contract.

## Storage Limitations

Data is stored in memory and is lost when the application restarts.
The application must run as a single process.

Each application instance owns separate repositories.
Multiple worker processes would not share their data.

Refresh-token rotation is implemented.
Session consumption and rotation are atomic within the current
in-memory repository implementation.
Separate application processes do not share refresh sessions.

Goal 8 replaces in-memory storage with PostgreSQL.

## Requirements

- Python 3.14, or permission for uv to install it.
- uv.
- Make for the documented one-command startup.
- Git for cloning the repository.

## Local Configuration

Run all commands from the repository root.

For the first local start:

```bash
make dev
```

This command installs dependencies from `uv.lock`, creates `.env` from
`.env.example` if needed, generates a local JWT secret, and starts the server.

If `.env` already exists, it is preserved without changes.
Invalid existing settings must be corrected manually.

For setup without starting the server:

```bash
make setup
make init-env
```

Do not commit `.env`.
Environment variables override values from `.env`.
Tests use isolated settings and do not require a local `.env`.

These commands configure a local development environment.
Data remains in memory and is lost when the application restarts.

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
uv run --locked mypy src tests scripts
uv run --locked pytest --cov=reelshelf --cov-report=term-missing --cov-fail-under=80
```

## Format

```bash
make format
```

## Design

- [Domain model and business rules](docs/domain.md)
- [API contract](docs/api.md)
- [Architecture and dependency rules](docs/architecture.md)
- [Watchlist endpoint behaviour](docs/entries.md)
- [Automated and live HTTP verification](docs/verification.md)

## Roadmap

Goal 7 delivers authentication and private watchlists using in-memory
repositories.

Goal 8 adds PostgreSQL, async SQLAlchemy, Alembic, Docker Compose,
CI, structured logging, and database readiness checks.

## Register a User

```bash
curl -i -X POST http://127.0.0.1:8000/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"username":"viewer","password":"StrongPassword123!"}'
```

Registration returns `201 Created` with the user's ID, normalized
username, and creation timestamp.

Duplicate usernames return `409 Conflict`.
Invalid requests return `422 Unprocessable Entity`.

Passwords are stored as Argon2 hashes and are never returned.
Registration does not issue tokens. Log in to obtain a token pair.
Users are lost when the application restarts.


## Authentication

Register with `POST /api/v1/auth/register`, then log in with
`POST /api/v1/auth/login`. Login returns `access_token`, `refresh_token`,
and `token_type: "bearer"`.

Send the access token in the `Authorization: Bearer <token>` header
to call `GET /api/v1/users/me`.

Send `{"refresh_token": "<token>"}` to `POST /api/v1/auth/refresh`
to obtain a new token pair. Replace the old refresh token immediately.
Replaying a consumed refresh token revokes that login's refresh family.
Separate logins have separate families. Rotation preserves the original
family expiration time.

Send the same request shape to `POST /api/v1/auth/logout`.
Success returns HTTP 204 with an empty body. Logout revokes the refresh
family; existing access tokens remain valid until expiration.

Refresh sessions are stored in memory and are lost on application restart.