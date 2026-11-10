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

## List entries

`GET /api/v1/entries`

Requires an access token. Only entries owned by the authenticated
user are returned.

### Query parameters

| Parameter | Default | Accepted values |
| --- | --- | --- |
| `status` | No filter | `planned` or `watched` |
| `limit` | `20` | Integer from 1 to 100 |
| `offset` | `0` | Non-negative integer |

Unknown query parameters are rejected.

Example:

```http
GET /api/v1/entries?status=planned&limit=10&offset=0
```

### Response

A successful request returns `200 OK` with:

- `items`: entries on the requested page.
- `total`: number of the user's entries matching the filter,
  before pagination.
- `limit`: requested page size.
- `offset`: requested number of entries to skip.

Entries are ordered by `created_at` descending, then by `id`
descending to resolve equal timestamps.

An empty collection returns:

```json
{
  "items": [],
  "total": 0,
  "limit": 20,
  "offset": 0
}
```

An offset beyond the matching collection returns an empty `items`
array while preserving the matching `total`.

Offset pagination does not provide a fixed snapshot across requests.
Adding or deleting entries between requests may shift page boundaries.

### Errors

- `401 Unauthorized`: access credentials are missing or invalid.
- `422 Unprocessable Content`: query parameters are invalid.

All errors use the application's shared error response format.


## Get an entry

`GET /api/v1/entries/{entry_id}`

Requires an access token in the
`Authorization: Bearer <token>` header.

### Path parameter

`entry_id` must be a valid UUID.

### Successful response

Returns `200 OK` with the existing entry:

- `id`
- `user_id`
- `title`
- `release_year`
- `status`
- `rating`
- `created_at`
- `updated_at`

Only the owner can retrieve the entry.
Reading an entry does not change its timestamps.

### Errors

- `401 Unauthorized`: access credentials are missing or invalid.
- `404 Not Found`: the entry does not exist or belongs to another user.
- `422 Unprocessable Content`: the entry ID is not a valid UUID.

Missing and foreign entries return the same response:

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Watchlist entry not found."
  }
}
```

## Update an entry

`PATCH /api/v1/entries/{entry_id}`

Requires an access token. Only the owner can update an entry.

### Request

All fields are optional, but at least one field must be provided.

| Field | Accepted values |
| --- | --- |
| `title` | Non-empty trimmed string, up to 200 characters |
| `release_year` | Integer from 1888 to 2100, or null |
| `status` | `planned` or `watched` |
| `rating` | Integer from 1 to 10, or null |

Omitted fields retain their current values.
Explicit null clears `release_year` or `rating`.
Explicit null is rejected for `title` and `status`.
Unknown fields are rejected.

Example:

```json
{
  "status": "watched",
  "rating": 9
}
```

Only watched entries can have a rating.
To move a rated entry back to planned, clear its rating in the same request:

```json
{
  "status": "planned",
  "rating": null
}
```

### Response

Returns `200 OK` with the complete updated entry.

The ID, owner, and creation timestamp are preserved.
The update timestamp changes when the entry's values change.
A request containing only existing values leaves the entry unchanged.

Rejected requests do not modify the stored entry.

### Errors

- `401 Unauthorized`: access credentials are missing or invalid.
- `404 Not Found`: the entry is missing or belongs to another user.
- `422 Unprocessable Content`: invalid input or a business rule violation.

An empty JSON object is rejected with `422`.



## Delete an entry

`DELETE /api/v1/entries/{entry_id}`

Requires an access token in the
`Authorization: Bearer <token>` header.

Only the owner can delete an entry.
The request does not require a body.

### Successful response

Returns `204 No Content` with an empty response body.

Do not attempt to parse the successful response as JSON.

After deletion:

- Retrieving the entry returns `404`.
- The entry no longer appears in list responses.
- Other entries remain unchanged.

### Repeated deletion

Deleting an already deleted entry returns `404 Not Found`.
The final state remains the same: the entry is absent.

### Errors

- `401 Unauthorized`: access credentials are missing or invalid.
- `404 Not Found`: the entry is missing or belongs to another user.
- `422 Unprocessable Content`: the entry ID is not a valid UUID.

Missing and foreign entries return the same error response:

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Watchlist entry not found."
  }
}
```


## Watchlist summary

`GET /api/v1/entries/summary`

Requires an access token in the `Authorization: Bearer <token>` header.

Returns statistics for all entries owned by the authenticated user.
The operation does not use list pagination or status filtering.

### Response

```json
{
  "total": 4,
  "planned": 1,
  "watched": 3,
  "average_rating": 8.5
}
```

- `total`: number of owned entries.
- `planned`: number of planned entries.
- `watched`: number of watched entries.
- `average_rating`: arithmetic mean of non-null ratings.

Unrated entries are excluded from the average.
The average is not explicitly rounded.
If no ratings exist, `average_rating` is null.

An empty watchlist returns zero counts and a null average.
Foreign entries do not affect any result.
Reading the summary does not modify entries.

### Errors

- `401 Unauthorized`: access credentials are missing or invalid.