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

- User registration at `POST /api/v1/auth/register`.
- Username normalization and request validation.
- Argon2 password hashing outside the event-loop thread.
- Duplicate username protection.
- Public user responses without password hashes.
- Password adapter, service, and registration API tests.

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
Registration does not issue tokens yet.
Users are lost when the application restarts.


## Authentication

Register a user with `POST /api/v1/auth/register`.
Log in with `POST /api/v1/auth/login`.

Login currently returns an access token and `token_type: "bearer"`.
Send the token in the `Authorization: Bearer <token>` header.

`GET /api/v1/users/me` returns the authenticated user's public profile.

Access tokens use HS256 and include subject, token ID, issue time,
expiration, issuer, audience, and token type claims.

Invalid, expired, or incorrectly signed tokens return 401.
A token is also rejected if its user no longer exists.

Refresh tokens and rotation are implemented in the next stage.