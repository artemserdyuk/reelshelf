# Project verification

Run all commands from the repository root.

## Full quality checks

```bash
make check
```

This runs linting, formatting checks, static type checks, tests,
and the configured coverage threshold.

## User journey without a running server

```bash
uv run --locked pytest tests/e2e/test_user_journey.py -v -s --tb=short
```

By default, the test uses the existing TestClient fixture.
It runs against a fresh application with test settings and does
not require a listening HTTP server.

## User journey against a running server

Start the development server in one terminal:

```bash
make run
```

Wait for `Application startup complete`.

In another terminal, run:

```bash
E2E_BASE_URL=http://127.0.0.1:8000 uv run --locked pytest tests/e2e/test_user_journey.py -v -s --tb=short
```

The environment variable applies only to this command.
Do not add it to the application's Settings or .env file.

This mode sends real HTTP requests using httpx.

## Covered workflow

- Register and log in two users.
- Create, retrieve, list, update, and delete entries.
- Verify that another user cannot access the owner's entries.
- Reject a rating for a planned entry without changing its data.
- Filter watched entries.
- Mark an entry as watched through the dedicated endpoint.
- Repeat the mark-watched action and preserve the existing rating.
- Verify summary counts and average rating.
- Clear a rating through the dedicated endpoint.
- Repeat the clear-rating action without changing the entry.
- Verify that clearing the last rating produces a null average.
- Rotate tokens and continue using the same user's data.
- Log out and reject further refresh attempts for that session.
- Log in again and retrieve the remaining entry.
- Delete the remaining entry and verify an empty list.

Logout revokes the refresh session.
An already issued access token remains valid until expiration.

## Expected result

The user journey reports `1 passed`.

Expected negative responses such as 401, 404, and 422 are part
of the scenario and do not indicate a failed test.

## In-memory storage

Do not edit source files during the live check.
Automatic reload restarts the application and clears its data.

Each run creates unique test users.
On success, the scenario deletes its entries.
Users and sessions remain in memory until the server restarts.

If the scenario fails, its partially created data may remain.
Unique usernames allow the next run to start independently.

Coverage is measured using the regular in-process test suite.
A separate running server is not included in that coverage measurement.


## Clean checkout verification

Use a separate clone with no `.env` and no `.venv`.

From its repository root, run:

```bash
make dev
```

Wait for `Application startup complete`.

In a second terminal, change to the same clone and run:

```bash
make check
E2E_BASE_URL=http://127.0.0.1:8000 uv run --locked pytest tests/e2e/test_user_journey.py -v -s --tb=short
```

Open `/docs` and compare the documented request and response shapes
with `docs/api.md`.

The API contains 13 business operations under `/api/v1`,
plus the liveness operation at `/health/live`.

Do not edit Python files during the live scenario:
automatic reload clears the in-memory data.

## Goal 7 acceptance checklist

Mark each item only after completing the check.

- [ ] A clean checkout starts with `make dev`.
- [ ] Re-running environment initialization preserves the existing `.env`.
- [ ] Ruff, formatting checks, strict mypy, and tests pass.
- [ ] Application coverage is at least 80%.
- [ ] The complete user journey passes against a running HTTP server.
- [ ] Swagger matches the implemented API contract.
- [ ] Domain, API, architecture, and setup documentation match the code.
- [ ] The three extension endpoints have been implemented independently
      without consulting solutions, then reviewed against the architecture note.
- [ ] Repository visibility and the review URL satisfy the IDP requirement.

## Goal 8 handoff

Keep the existing API behaviour while replacing in-memory persistence.

The next phase introduces:

- SQLAlchemy 2.x async models and PostgreSQL repositories using asyncpg.
- Alembic migrations, including upgrade and downgrade verification.
- Transaction boundaries for multi-step operations such as refresh rotation.
- Database tests and service tests using AsyncMock.
- Hand-written SQL comparisons for three expensive operations.
- A multi-stage Docker image and Docker Compose.
- GitHub Actions with lint, type, test, coverage, and image-build checks.
- Structured JSON logs with request correlation IDs.
- A readiness endpoint that checks database connectivity.