# ReelShelf — API Contract

All paths below are relative to `/api/v1`.
Protected endpoints require `Authorization: Bearer <access_token>`.
Request and response bodies use JSON.

## Shapes

- RegisterRequest:
  {username: string, password: string}
  Username: normalized, 3–30 characters.
  Password: 8–128 characters; never trimmed.

- LoginRequest:
  {username: string, password: string}

- RefreshRequest:
  {refresh_token: string}

- UserResponse:
  {id: UUID, username: string, created_at: datetime}

- TokenPair:
  {access_token: string, refresh_token: string, token_type: "bearer"}

- EntryCreate:
  {title: string, release_year?: integer | null}

- EntryPatch:
  {title?: string, release_year?: integer | null,
   status?: "planned" | "watched", rating?: integer | null}
  At least one field is required.
  Omitted fields remain unchanged.
  Null is allowed only for release_year and rating.

- EntryResponse:
  {id: UUID, title: string, release_year: integer | null,
   status: "planned" | "watched", rating: integer | null,
   created_at: datetime, updated_at: datetime}

- EntryPage:
  {items: EntryResponse[], total: integer, limit: integer, offset: integer}

- SummaryResponse:
  {total: integer, planned: integer, watched: integer,
   average_rating: number | null}

- ErrorResponse:
  {error: {code: string, message: string}}

## Endpoints

| Phase | Method | Path | Auth | Input | Success | Errors |
|---|---|---|---|---|---|---|
| Core | POST | /auth/register | No | RegisterRequest | 201 UserResponse | 409, 422 |
| Core | POST | /auth/login | No | LoginRequest | 200 TokenPair | 401, 422 |
| Core | POST | /auth/refresh | No | RefreshRequest | 200 TokenPair | 401, 422 |
| Core | POST | /auth/logout | No | RefreshRequest | 204, no body | 401, 422 |
| Core | GET | /users/me | Yes | None | 200 UserResponse | 401 |
| Core | POST | /entries | Yes | EntryCreate | 201 EntryResponse | 401, 422 |
| Core | GET | /entries | Yes | status?, limit=20, offset=0 | 200 EntryPage | 401, 422 |
| Core | GET | /entries/{entry_id} | Yes | UUID path parameter | 200 EntryResponse | 401, 404, 422 |
| Core | PATCH | /entries/{entry_id} | Yes | UUID + EntryPatch | 200 EntryResponse | 401, 404, 422 |
| Core | DELETE | /entries/{entry_id} | Yes | UUID path parameter | 204, no body | 401, 404, 422 |
| Memory | GET | /entries/summary | Yes | None | 200 SummaryResponse | 401 |
| Memory | POST | /entries/{entry_id}/watched | Yes | UUID, no body | 200 EntryResponse | 401, 404, 422 |
| Memory | DELETE | /entries/{entry_id}/rating | Yes | UUID, no body | 200 EntryResponse | 401, 404, 422 |

## Behaviour

- Unknown request-body fields are rejected.
- limit must be between 1 and 100; offset must be non-negative.
- Lists are ordered by created_at descending, then id descending.
- total is the number of matching entries before pagination.
- Ratings are strict integers from 1 to 10.
- A non-null rating requires the resulting status to be watched.
- Setting status to planned clears an existing rating.
- Sending status planned with a non-null rating returns 422.
- Marking an already watched entry is idempotent and preserves its rating.
- Clearing an absent rating is idempotent.
- Summary counts only the current user's entries.
- average_rating excludes entries without a rating and is null when none exist.
- Static routes such as /entries/summary precede /entries/{entry_id}.
- Logout authenticates through its refresh token, not an access header.
- Missing, expired, malformed, or incorrectly signed access tokens return 401.
- Access and refresh tokens cannot be used interchangeably.
- Framework 404/405 and unexpected 500 errors use ErrorResponse.
- Unexpected errors never expose internal exception details.

## Infrastructure

`/health/live` is outside API versioning and is not a business endpoint.
Goal 8 adds `/health/ready`, which checks database connectivity.