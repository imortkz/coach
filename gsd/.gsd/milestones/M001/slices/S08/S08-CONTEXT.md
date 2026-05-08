---
id: S08
milestone: M001
status: ready
---

# S08: Authentication and Multi-User — Context

## Goal

Add Telegram Login Widget authentication with JWT sessions, multi-user data isolation via user_id on all documents, and a dev-mode auth bypass for localhost development.

## Why this Slice

S07 delivers the MongoDB data layer with Beanie ODM. S08 layers authentication and per-user data scoping on top. Without auth, the app remains single-user and cannot be deployed for others. S09 (Docker deployment) depends on auth being wired so the full stack can be verified end-to-end.

## Scope

### In Scope

- **Telegram Login Widget** on a full-page login gate — unauthenticated users see only the login page, no app content
- **Backend auth module** (`app/auth/`): Telegram HMAC-SHA-256 verification, JWT creation/validation with PyJWT, `get_current_user` FastAPI dependency
- **User collection** in MongoDB: auto-create user document on first Telegram login (telegram_id, first_name, username, photo_url)
- **JWT sessions**: 1-year expiry, stored in localStorage, sent as `Authorization: Bearer <token>` header
- **user_id field** added to all documents (exercises, programs, workouts, settings); all queries filter by user_id
- **Seed exercises shared globally** — seed exercises have no user_id, visible to all users; custom exercises scoped per-user
- **Dev-mode auth bypass**: when `ENVIRONMENT=dev`, backend auto-creates a test user and frontend skips login entirely (silent auto-login, zero friction)
- **Frontend auth integration**: auth store (Pinia), `useApi` composable for centralized Bearer token injection, router navigation guard redirecting unauthenticated users to `/login`
- **User identity display**: small avatar + first name in nav bar top-right corner
- **Logout**: tapping user avatar shows "Log out" option, clears token, redirects to login page
- **401 handling**: on any 401 API response, clear token and redirect to login page
- **Compound MongoDB indexes** with user_id prefix on exercises, programs, workouts collections

### Out of Scope

- SSL/TLS — deferred to future milestone (requires domain)
- User profile page or account settings
- Refresh token rotation — single long-lived JWT is sufficient for threat model
- Role-based access control — flat user model, everyone equal
- Admin dashboard
- Exercise sharing between users
- Data migration from SQLite (handled by S07's clean start decision — DB-06)

## Constraints

- Telegram Login Widget requires a registered bot via @BotFather with `/setdomain` configured — this is a manual prerequisite before the widget works in production
- Dev-mode bypass must be env-guarded (`ENVIRONMENT=dev`) and must never activate in production
- PyJWT for tokens (D011), not python-jose
- JWT stored in localStorage (D013), not httpOnly cookie
- All 4 existing frontend stores use raw `fetch()` — must be migrated to use `useApi` composable for auth header injection
- S07 must be complete before S08 starts (MongoDB + Beanie documents must be operational)

## Integration Points

### Consumes

- `app/exercises/models.py` (Beanie Document) — add user_id field, update queries
- `app/programs/models.py` (Beanie Document) — add user_id field, update queries
- `app/workouts/models.py` (Beanie Document) — add user_id field, update queries
- `frontend/src/stores/*.ts` — existing stores to wrap with useApi
- `frontend/src/router/index.ts` — add auth guard
- `frontend/src/App.vue` — add user display in nav bar

### Produces

- `app/auth/` module — routes.py, dependencies.py, telegram.py, jwt.py
- `app/auth/dependencies.py` → `get_current_user` FastAPI dependency used by all routes
- `frontend/src/stores/auth.ts` — login state, token storage, user info
- `frontend/src/composables/useApi.ts` — centralized fetch with Authorization header
- `frontend/src/views/LoginView.vue` — Telegram Login Widget page
- MongoDB `users` collection with telegram_id unique index

## Open Questions

- **Popup blocker handling**: Telegram widget opens a popup — if blocked, what feedback does the user see? Current thinking: show a small text hint "If login didn't open, check your popup blocker" below the widget.
- **Settings migration**: v1.0 settings are a global key-value table. In multi-user, should settings become per-user fields on the user document, or stay as a separate collection with user_id? Current thinking: per-user fields on user document (only setting is rest_timer_disabled which is already on programs).
