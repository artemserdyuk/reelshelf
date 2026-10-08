# ReelShelf — Domain

## Purpose

ReelShelf is a REST API for managing personal movie watchlists.
Users can track movies they plan to watch, mark them as watched,
and record ratings.

## Entities

### User

Fields:
- id: UUID
- username: normalized unique string, 3–30 characters
- password_hash: string
- created_at: timezone-aware UTC datetime

Usernames are trimmed and converted to lowercase.
Passwords are hashed with Argon2 and are never returned by the API.

### WatchlistEntry

Fields:
- id: UUID
- user_id: UUID
- title: trimmed string, 1–200 characters
- release_year: integer from 1888 to 2100, or null
- status: planned or watched
- rating: integer from 1 to 10, or null
- created_at: timezone-aware UTC datetime
- updated_at: timezone-aware UTC datetime

Each entry belongs to exactly one user.
Duplicate titles are allowed.

### RefreshSession

Fields:
- jti: UUID identifying a refresh token
- family_id: UUID identifying a login session and its rotated tokens
- user_id: UUID
- expires_at: timezone-aware UTC datetime
- used_at: timezone-aware UTC datetime, or null
- revoked_at: timezone-aware UTC datetime, or null

Raw refresh tokens are not stored.

## Business Rules

- Users can access only their own watchlist entries.
- Missing entries and entries owned by another user both return 404.
- New entries start with status planned and no rating.
- Only watched entries may have a rating.
- Moving an entry back to planned clears its rating.
- A refresh token may be used successfully only once.
- Refreshing consumes the current refresh token and issues a new token pair.
- Reuse of a consumed refresh token revokes its entire session family.
- Logout revokes the session family identified by a valid refresh token.
- Issued access tokens remain valid until their expiration.

## Goal 7 Scope

- Registration, login, refresh rotation, and logout.
- Current-user endpoint.
- Private watchlist CRUD.
- Filtering and pagination.
- Three later extensions: summary, mark watched, and clear rating.
- In-memory repositories.
- Automated tests and setup documentation.

## Out of Scope

- Frontend application.
- Shared watchlists and social features.
- External movie APIs.
- Password reset and email verification.
- Recommendations and background jobs.
- Database and deployment infrastructure during Goal 7.

## Goal 8 Extension

Replace in-memory repositories with PostgreSQL repositories using
async SQLAlchemy. Add Alembic migrations, database tests, Docker Compose,
CI checks, structured logging, and liveness/readiness endpoints.