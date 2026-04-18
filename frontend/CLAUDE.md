# Frontend

Vue 3 + TypeScript admin dashboard. Vite build, Pinia state management, file-based routing via `unplugin-vue-router`, Tailwind + Reka UI components.

## Commands

```bash
npm run dev       # dev server on :5173 (proxies /v1 → localhost:8000)
npm run build     # production build
npm run typecheck # tsc --noEmit
```

## Project Structure

```
src/
├── api/          # Axios client + domain API modules (auth, users, roles, organizations, billing)
├── components/
│   ├── ui/       # Base shadcn-style components (Button, Input, Dialog, Card, etc.)
│   ├── common/   # Shared app components (DataTable, PageHeader, ConfirmDialog, PermissionGuard)
│   ├── layout/   # AppSidebar, AppTopbar, MobileSidebar
│   ├── users/    # Domain components
│   ├── roles/
│   └── organizations/
├── composables/  # useDataTable, useErrorHandler, usePermission, useConfirm
├── layouts/      # DashboardLayout, AuthLayout
├── locales/      # i18n strings (en, da)
├── pages/        # File-based routes — each .vue file = a route
├── plugins/      # i18n setup
├── router/       # Router config + navigation guards
├── stores/       # auth.ts (user, token, permissions, organizations), ui.ts (sidebar)
└── types/        # Shared TypeScript types
```

## Routing

Routes are auto-generated from `src/pages/**/*.vue` by `unplugin-vue-router`. No manual route definitions — adding a file creates a route.

Route metadata is declared with YAML frontmatter in each page file:

```vue
<route lang="yaml">
meta:
  layout: dashboard        # 'dashboard' | 'auth'
  requiresAuth: true
  permission: users:read   # optional — guards the route
  breadcrumb: nav.users
</route>
```

The router guard in `src/router/index.ts` enforces `requiresAuth`, `guestOnly`, and `permission` checks.

## State Management

**`stores/auth.ts`** — Auth + authorization:
- `user`, `accessToken`, `permissions[]`, `organizations[]`
- `initialize()` — silent refresh from httponly cookie (called once on app load)
- `login()` / `logout()` / `switchOrganization()`
- `hasPermission(name)` — checks flattened permissions from user roles

**`stores/ui.ts`** — UI state:
- `sidebarOpen` — mobile sidebar toggle

## API Layer

`src/api/client.ts` — Axios instance with:
- Request interceptor: attaches `Authorization: Bearer <token>`
- Response interceptor: on 401, queues concurrent requests, refreshes token, retries — or clears session and redirects to login on failure
- `withCredentials: true` for httponly refresh token cookie

API modules (`api/auth.ts`, `api/users.ts`, etc.) export plain functions that call the shared client. Add new endpoints in the relevant domain module.

## Components

### UI Components (`components/ui/`)
Headless Reka UI + Radix Vue primitives styled with Tailwind. Do not modify these unless fixing a bug — treat as a library.

### Common Components
- **`DataTable`** — generic paginated table. Use with `useDataTable` composable for fetch/sort/filter/pagination logic
- **`PageHeader`** — standard page title + action slot
- **`ConfirmDialog`** — global confirmation modal, triggered via `useConfirm()`
- **`PermissionGuard`** — wraps content that requires a permission: `<PermissionGuard permission="users:write">`
- **`EmptyState`** — empty list state with title + description

### Writing Components
- Use `<script setup lang="ts">` exclusively
- Props: `defineProps<{ ... }>()`
- Emit types: `defineEmits<{ (e: 'update', val: string): void }>()`
- Loading state: local `ref<boolean>` + disable interactive elements during async ops
- Errors: catch in try/catch, pass to `useErrorHandler()` for translated toast messages

## Forms

Use VeeValidate + Zod:

```ts
import { useForm } from 'vee-validate'
import { toTypedSchema } from '@vee-validate/zod'
import * as z from 'zod'

const schema = z.object({ email: z.string().email() })
const { handleSubmit, errors } = useForm({ validationSchema: toTypedSchema(schema) })
```

Field errors render inline. API errors go through `useErrorHandler` → toast.

## Permissions

Check in templates with `PermissionGuard`, in logic with `usePermission()`:

```ts
const { hasPermission } = usePermission()
if (hasPermission('billing:write')) { ... }
```

Permission names follow `resource:action` convention (e.g., `users:read`, `roles:write`).

## Internationalization

All user-facing strings go through `vue-i18n`. Use `const { t } = useI18n()` in script, `$t('key')` in templates. Add keys to both `src/locales/en.json` and `src/locales/da.json`.

Key namespaces: `auth.*`, `nav.*`, `common.*`, `settings.*`, `errors.api.*`, `errors.fields.*`

## Styling

Tailwind CSS with a CSS variable-based theme (HSL tokens defined in `src/assets/index.css`). Use `cn()` from `@/lib/utils` to merge classes conditionally. Dark mode is supported via the theme variables.

## Conventions

- **Components**: PascalCase filenames
- **Pages**: kebab-case filenames
- **Composables/utilities**: camelCase, `use` prefix for composables
- **API modules**: camelCase with `Api` suffix (e.g., `usersApi`)
- Path alias `@` maps to `src/`
- Auto-imported: Vue reactivity APIs, vue-router composables, Pinia helpers — no explicit imports needed for these
- Auto-registered: all components in `src/components/` — no explicit imports needed
