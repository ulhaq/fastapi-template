# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Structure

Full-stack multi-tenant SaaS application:
- `backend/` — FastAPI + Python, PostgreSQL, async SQLAlchemy, Alembic migrations. See `backend/CLAUDE.md`.
- `frontend/` — Vue 3 + TypeScript, Vite, Pinia, file-based routing. See `frontend/CLAUDE.md`.

Each subdirectory has its own CLAUDE.md with commands, architecture, and conventions specific to that layer.

## Quick Commands

### Backend (`cd backend` first)
```bash
uv run pytest ./tests                                          # all tests
uv run pytest ./tests/api/test_auth.py::test_name -v          # single test
./scripts/lint.sh                                              # mypy + ruff + pylint
./scripts/format.sh                                           # format
uv run fastapi dev src/main.py --host 0.0.0.0 --port 8000     # dev server
alembic revision --autogenerate -m "description"              # new migration
alembic upgrade head                                          # apply migrations
python -m src.init_db                                         # reset + seed DB
```

### Frontend (`cd frontend` first)
```bash
npm run dev        # dev server on :5173, proxies /v1 → localhost:8000
npm run build      # production build
npm run typecheck  # tsc --noEmit
```

## Architecture Overview

### Backend: Routers → Services → Repositories → Models

- **Routers** (`src/routers/`) — HTTP layer; validate input, delegate to services
- **Services** (`src/services/`) — Business logic; raise `ClientException(ErrorCode.X)` on failures
- **Repositories** (`src/repositories/`) — SQLAlchemy queries; enforce org isolation via `organization_id`
- **Models** (`src/models/`) — SQLAlchemy ORM entities with soft-delete (`deleted_at`)
- **Schemas** (`src/schemas/`) — Pydantic V2 request/response models
- **Core** (`src/core/`) — Config, JWT security, DI dependencies (`authenticate()`, `require_permission()`), error middleware

Generic base classes `ResourceService[T]` and `SQLResourceRepository[T]` handle standard CRUD; domain classes extend them.

### Frontend: Pages → Composables → API → Stores

- **Pages** (`src/pages/`) — File-based routing; each `.vue` file = a route with YAML `<route>` frontmatter for layout/auth/permission metadata
- **Composables** (`src/composables/`) — `useDataTable`, `useErrorHandler`, `usePermission`, `useConfirm`
- **API** (`src/api/`) — Axios client with token interceptor + silent refresh; domain modules per resource
- **Stores** (`src/stores/`) — `auth.ts` (user, token, permissions, orgs), `ui.ts` (sidebar)

### Cross-Cutting Concerns

**Multi-tenancy** — All resources belong to an `Organization`. Isolation is enforced at the repository layer; services receive `organization_id` from the authenticated user context.

**RBAC** — `Permission` enum in `backend/src/enums.py` defines all permissions (`resource:action`). Backend enforces via `require_permission()` dependency; frontend guards with `<PermissionGuard>` and `usePermission()`.

**Error flow** — Backend raises `ClientException(ErrorCode.X)` → middleware serializes to JSON → frontend `useErrorHandler()` maps `errors.api.*` i18n keys to toast messages.

**Testing** — Backend tests use SQLite in-memory with pre-seeded fixtures; no external services needed. Mock email/Stripe calls with `mocker.patch()`.

**Database migrations** — Add columns/tables in models, then `alembic revision --autogenerate`. Prefer adding to an existing staged migration file over creating a new one.
