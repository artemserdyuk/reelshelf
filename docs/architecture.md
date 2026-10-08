# ReelShelf — Architecture

## Structure

The application uses routers, services, repositories, and schemas.
Domain entities and repository protocols define internal contracts.
The composition layer creates and connects concrete implementations.

## Layers and Import Rules

| Layer | Responsibility | Allowed imports | Forbidden patterns |
|---|---|---|---|
| Routers | HTTP input/output, dependencies, response mapping | FastAPI, schemas, services, API dependencies | Storage access, business decisions |
| Schemas | Validate and describe API input/output | Pydantic, domain enums, standard library | Repository calls, token operations, database access |
| Services | Business rules and use-case orchestration | Domain entities, errors, repository/security protocols | FastAPI, HTTPException, Request, SQLAlchemy, concrete repositories |
| Repository protocols | Define persistence operations | Domain entities, typing, standard library | HTTP and database implementation details |
| Repository implementations | Read and write stored data | Domain contracts, storage libraries | HTTP responses and request parsing |
| Security adapters | Hash passwords and encode/decode tokens | Security protocols, security libraries, settings | HTTP response generation |
| API dependencies | Resolve current user and construct services | FastAPI, services, adapters, app container | Duplicated business rules |
| Composition | Configure the app and connect implementations | All layers | Business rules |

## Data Flow

Routers validate requests with schemas and call services.
Services enforce rules and call repository protocols.
Repositories return domain entities.
Routers map results to response schemas.

Services raise domain exceptions.
Central API exception handlers map them to HTTP status codes
and the shared error response.

## Persistence Boundary

Only repository implementations read or mutate backing stores.
Services may work with returned domain entities but must persist
changes through repository methods.

In-memory repositories return detached values so that mutation
cannot silently change stored state.

Repository methods are asynchronous to support the later database adapter.
This does not make CPU-bound password hashing non-blocking;
security adapters must offload that work appropriately.

## Dependency Lifetime

Settings and the Goal 7 repository container belong to one app instance.
Requests resolve services using that container.
Tests create a fresh app and fresh stores to avoid shared state.

Goal 8 uses per-request database sessions.
Repositories do not independently commit multi-step use cases.
A unit-of-work boundary makes operations such as refresh rotation atomic.

## Goal 7 Limitations

Data is lost on restart.
The application runs in a single process.
In-memory refresh rotation must still consume tokens atomically.

## Goal 8 Migration

Add ORM models, async sessions, PostgreSQL repositories, migrations,
and a transactional unit of work.
Preserve HTTP contracts and domain behaviour where practical.