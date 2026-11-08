# Watchlist entries

## Create an entry

`POST /api/v1/entries`

Authentication: an access token in the `Authorization: Bearer <token>` header.

### Request

```json
{
  "title": "Arrival",
  "release_year": 2016
}
```

- `title` is required. Leading and trailing whitespace is removed.
  The resulting title must contain between 1 and 200 characters.
- `release_year` is optional and may be null.
  When provided as a non-null value, it must be an integer between
  1888 and 2100. Strings and booleans are rejected.
- Additional fields are rejected.

### Response

A successful request returns `201 Created` and an entry containing:

- `id`
- `user_id`
- `title`
- `release_year`
- `status`
- `rating`
- `created_at`
- `updated_at`

The owner is taken from the authenticated user.
New entries have status `planned` and a null rating.
Creation and update timestamps are initially equal and use UTC.

### Errors

- `401 Unauthorized`: access credentials are missing or invalid.
- `409 Conflict`: the generated entry ID conflicts with an existing ID.
- `422 Unprocessable Content`: the request fails validation.

Errors use the application's shared error response format.

### Storage

Entries are currently stored in memory and are lost when the
application process restarts. Separate processes do not share entries.

The service depends on the `EntryRepository` protocol so that a
database-backed repository can be introduced later.

Duplicate titles are currently allowed.