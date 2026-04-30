# FastAPI Backend Project Guide

This file provides comprehensive guidance for working with this FastAPI multi-tenant backend project.

## Project Overview

**FastAPI-based multi-tenant backend** with role-based access control (RBAC), JWT authentication, and async SQLAlchemy ORM. Designed for scalability with clean architecture, comprehensive testing, and production-ready patterns.

**Key Characteristics:**
- Multi-tenant architecture with enforced tenant isolation
- Fine-grained RBAC with granular permissions
- Async/await throughout using SQLAlchemy async drivers
- Pydantic V2 for schema validation
- Alembic for database migrations
- Comprehensive pytest suite with in-memory SQLite testing
- Type hints throughout (enforced via mypy)

---

## Architecture

### Layered Architecture: Routers > Services > Repositories > Models

The project follows a clean layered architecture: **Routers > Services > Repositories > Models**.

- `src/routers/` - FastAPI route handlers; validate HTTP input, delegate to services
- `src/services/` - Business logic; coordinate repositories, raise `ClientException` on failures
- `src/repositories/` - SQLAlchemy data access; handle filtering, pagination, soft deletes
- `src/models/` - SQLAlchemy ORM entities
- `src/schemas/` - Pydantic request/response models
- `src/core/` - Cross-cutting concerns: config, security (JWT/passwords), DI dependencies, error handling, rate limiting

### Key patterns

**Generic base classes** - `ResourceService[T]` and `SQLResourceRepository[T]` provide standard CRUD behavior. Domain-specific classes extend these; avoid duplicating CRUD logic.

**Dependency injection** - `src/core/dependencies.py` provides `authenticate()` and `require_permission(Permission.X)` FastAPI dependencies for auth/authz. `RepositoryManager` in `src/repositories/repository_manager.py` is the DI container for repositories.

**Error handling** - Raise `ClientException(ErrorCode.X)` from services; the middleware in `src/core/middlewares.py` converts these to consistent JSON error responses. Error codes are defined in `src/enums.py`.

**Multi-tenancy** - Users and resources belong to a `Organization`. Organization isolation is enforced at the repository level via `organization_id` foreign keys.

**Permissions** - Fine-grained RBAC using the `Permission` enum (`src/enums.py`). Users have roles; roles have permissions. Use `require_permission()` on routes to enforce access.

**Query features** - Repositories support dynamic filtering via `ComparisonOperator` (eq, lt, gte, contains, in, between, etc.), pagination (`page_number`, `page_size`), and sorting. The `/v1/query-options` endpoint exposes filterable fields to the frontend.

### Database migrations
Add columns/tables in models, then `alembic revision --autogenerate`.
Prefer adding to an existing staged migration file over creating a new one.

### Testing
- Tests use **SQLite in-memory** database; no external DB needed
- `tests/conftest.py` provides: async test client, pre-seeded organizations/users/roles/permissions, and per-test DB teardown
- `asyncio_mode = auto` (set in `pytest.ini`); all test functions can be `async`


## Commands (`cd backend` first)

```bash
# Format code
./scripts/format.sh

# Lint (mypy + ruff)
./scripts/lint.sh

# Run all tests
uv run pytest ./tests

# Run a single test
uv run pytest ./tests/api/test_auth.py::test_register_an_account -v

# Database setup (runs migrations + seeds data)
python -m src.init_db

# Drop all tables
python -m src.init_db drop

# Start dev server
uv run fastapi dev src/main.py --host 0.0.0.0 --port 8000

# Database migrations
alembic revision --autogenerate -m "description"   # Create migration
alembic upgrade head                               # Apply migrations
alembic downgrade -1                               # Rollback last migration
```

**Package manager:** `uv` (use `uv add`, `uv run`, etc.)

---