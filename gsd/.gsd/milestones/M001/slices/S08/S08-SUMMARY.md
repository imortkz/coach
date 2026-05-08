---
id: S08
parent: M001
milestone: M001
provides:
  - Telegram Login Widget auth with HMAC-SHA-256 verification
  - JWT session tokens (1-year expiry) stored in localStorage
  - User model (MongoDB) with auto-create on first Telegram login
  - get_current_user FastAPI dependency on all protected routes
  - user_id field on Program, Workout, Setting documents; nullable on Exercise (shared seed)
  - Dev-mode auth bypass: DEV_MODE=true + /api/auth/dev-login + router guard auto-login
  - Frontend LoginView, auth store, apiFetch utility, router guards
requires:
  - slice: S07
    provides: All endpoints async MongoDB/Beanie; program versioning; exercise/program/workout models
affects:
  - S09
key_files:
  - backend/app/auth/__init__.py
  - backend/app/auth/models.py
  - backend/app/auth/jwt.py
  - backend/app/auth/telegram.py
  - backend/app/auth/dependencies.py
  - backend/app/auth/routes.py
  - backend/app/config.py
  - backend/app/database.py
  - backend/app/main.py
  - backend/app/exercises/models.py
  - backend/app/exercises/routes.py
  - backend/app/programs/models.py
  - backend/app/programs/routes.py
  - backend/app/workouts/models.py
  - backend/app/workouts/routes.py
  - backend/tests/conftest.py
  - backend/tests/test_auth.py
  - backend/tests/test_workouts.py
  - backend/tests/test_exercises.py
  - frontend/src/stores/auth.ts
  - frontend/src/composables/useApi.ts
  - frontend/src/lib/apiFetch.ts
  - frontend/src/views/LoginView.vue
  - frontend/src/router/index.ts
key_decisions:
  - Exercise.user_id is nullable (None = shared seeded exercise, non-null = user-owned custom)
  - python-jose[cryptography] used for JWT (not PyJWT as originally recorded in D011)
  - apiFetch reads localStorage directly so Pinia stores work outside Vue component context
  - Dev-mode router guard calls /api/auth/dev-login automatically on first navigation
patterns_established:
  - get_current_user dependency injected via Depends() on every protected route
  - user_id filter pattern: {"user_id": current_user.id, ...rest_of_query}
  - Shared resources (seed exercises) use user_id=None + $or query for list endpoints
observability_surfaces:
  - GET /api/auth/me — returns current user identity; useful for verifying auth state
  - DEV_MODE config flag — visible in startup config
  - POST /api/auth/dev-login — explicit dev bypass endpoint
drill_down_paths:
  - backend/tests/test_auth.py — auth endpoint and isolation tests
  - backend/app/auth/ — all auth logic
duration: ~2 hours
verification_result: passed
completed_at: 2026-03-13
---

# S08: Authentication and Multi-User

**Telegram Login Widget auth with JWT sessions, user-scoped data isolation on all documents, dev-mode bypass — 59 tests passing.**

## What Happened

S08 started with a clean MongoDB backend (from S07) and no auth whatsoever. The slice added a complete auth layer across backend and frontend.

**Backend auth module** (`app/auth/`): Four files — `models.py` (User document), `jwt.py` (create/decode tokens with python-jose), `telegram.py` (HMAC-SHA-256 verification per Telegram docs), `dependencies.py` (FastAPI `get_current_user` dependency with dev bypass), `routes.py` (POST /api/auth/telegram, POST /api/auth/dev-login).

**Model updates**: Added `user_id` field to `Program`, `Workout`, and `Setting` documents as required. `Exercise.user_id` is nullable — `None` means a shared/seeded exercise visible to all users; a non-null value means a user-owned custom exercise. The exercises list endpoint uses `$or: [{user_id: None}, {user_id: current_user.id}]` to return both.

**Route updates**: All exercises, programs, workouts, and settings routes now carry `Depends(get_current_user)`. Every query filters by `current_user.id`. Cross-user access returns 404 (not 403) to avoid leaking existence.

**Dev mode**: `DEV_MODE=true` (default) makes `get_current_user` return a dev user when no Bearer token is present. This means all 59 existing tests required no auth headers — only the conftest needed a `test_user` fixture to pre-create the dev user in the test DB.

**Frontend**: New `auth.ts` store handles token persistence (localStorage), dev login, Telegram login, and `fetchMe`. A `apiFetch` utility reads the token from localStorage so Pinia stores can attach `Authorization` headers without router context. `LoginView.vue` renders the Telegram widget or a dev-mode button. `router/index.ts` guards all routes: in dev mode, automatically calls `devLogin()` on first navigation so the user never sees the login page locally.

**Tests**: Added `test_auth.py` with 10 tests covering dev login, JWT auth, invalid token rejection, user isolation, and Telegram HMAC failure modes.

## Verification

- `uv run pytest tests/ -q` → **59 passed** (10 new auth tests + 49 from S07)
- `npm run build` → clean TypeScript build, no errors
- HMAC verification manually confirmed against real Telegram formula

## Requirements Advanced

- USER-03 — Basic user_id indexes added on all collections; compound prefix indexes deferred to S09

## Requirements Validated

- AUTH-01 — LoginView with Telegram widget rendered; routes confirmed in build
- AUTH-02 — verify_telegram_auth() with correct/incorrect hashes tested; 401 on bad hash confirmed
- AUTH-03 — 365-day JWT expiry; test_jwt_auth_valid_token passes
- AUTH-04 — User auto-created on first Telegram login; updated on subsequent logins
- AUTH-05 — get_current_user on all routes; test_jwt_auth_invalid_token_returns_401 passes
- AUTH-06 — DEV_MODE bypass tested with 59 tests running without auth headers
- USER-01 — user_id on Program, Workout, Setting; nullable on Exercise
- USER-02 — All queries filtered by user_id; isolation tests confirm cross-user 404
- VER-04 — Workout history now user-scoped (note updated)

## New Requirements Surfaced

- none

## Requirements Invalidated or Re-scoped

- USER-03 — Compound indexes deferred: simple `user_id` single-field indexes added. Compound prefix indexes (e.g. `(user_id, completed_at)`) will be added in S09 when Docker deployment reveals actual query patterns.

## Deviations

- `python-jose[cryptography]` was installed (D011 had recorded PyJWT as the plan). Both are functionally equivalent for HS256; python-jose was used. D015 recorded.
- `Exercise.user_id` is nullable rather than required — unplanned but necessary because seeded exercises have no owner. The `$or` list filter pattern handles this cleanly.
- The `/api/auth/me` endpoint is registered directly in `main.py` (not in `auth_router`) to avoid route collision with the auth module's placeholder. The placeholder was removed.

## Known Limitations

- Telegram auth is not live-tested end-to-end (requires a registered bot and deployed domain). The HMAC verification logic is unit-tested and correct per Telegram docs.
- USER-03 compound indexes not yet created — adds to S09 scope.
- `useApi` composable in `composables/useApi.ts` was created but not wired into views (views still use stores which use `apiFetch`). The composable exists for future use in views that make direct fetch calls.

## Follow-ups

- S09: Add compound indexes (user_id + completed_at, user_id + key) to Beanie Settings definitions
- S09: Set `DEV_MODE=false` in Docker production compose
- S09: Document Telegram bot setup prerequisite (DOCK-06)

## Files Created/Modified

- `backend/app/auth/__init__.py` — new auth module marker
- `backend/app/auth/models.py` — User Beanie document
- `backend/app/auth/jwt.py` — JWT create/decode (python-jose, HS256, 365d expiry)
- `backend/app/auth/telegram.py` — HMAC-SHA-256 Telegram login verification
- `backend/app/auth/dependencies.py` — get_current_user FastAPI dependency + dev bypass
- `backend/app/auth/routes.py` — POST /api/auth/telegram, POST /api/auth/dev-login
- `backend/app/config.py` — added JWT_SECRET, JWT_ALGORITHM, TELEGRAM_BOT_TOKEN, DEV_MODE, DEV_USER_ID
- `backend/app/database.py` — added User to init_beanie document_models
- `backend/app/main.py` — added auth_router; GET /api/auth/me; removed placeholder
- `backend/app/exercises/models.py` — added nullable user_id field + index
- `backend/app/exercises/routes.py` — auth dependency; $or query for shared+owned; user-scoped history
- `backend/app/programs/models.py` — added user_id field + index
- `backend/app/programs/routes.py` — auth dependency; all queries filter by user_id
- `backend/app/workouts/models.py` — added user_id to Workout and Setting; compound index on Setting
- `backend/app/workouts/routes.py` — auth dependency; user_id in all queries; compute_progression takes user_id param
- `backend/tests/conftest.py` — added User to init_beanie; test_user fixture; client depends on test_user
- `backend/tests/test_auth.py` — new: 10 tests for dev mode, JWT, isolation, Telegram HMAC
- `backend/tests/test_workouts.py` — updated: user_id on direct model inserts; test_user in fixtures
- `backend/tests/test_exercises.py` — updated: custom_exercise fixture uses DEV_USER_ID; program insert in test uses user_id
- `frontend/src/stores/auth.ts` — new: token persistence, devLogin, telegramLogin, fetchMe, logout
- `frontend/src/lib/apiFetch.ts` — new: authenticated fetch reading token from localStorage
- `frontend/src/composables/useApi.ts` — new: Vue-context auth fetch with router 401 redirect
- `frontend/src/views/LoginView.vue` — new: Telegram widget + dev mode button
- `frontend/src/router/index.ts` — added /login route; beforeEach guard with dev auto-login

## Forward Intelligence

### What the next slice should know
- DEV_MODE defaults to `true` — production Docker compose MUST set `DEV_MODE=false` and `JWT_SECRET` to a stable secret (not the random default)
- The Telegram widget requires `VITE_TELEGRAM_BOT_NAME` env var in the frontend build
- Exercise shared/custom split: seed exercises have `user_id=None`. Any scripts that insert seed data must leave user_id as None (not set to an admin user).
- `python-jose` is in pyproject.toml; it will appear in the Docker image.

### What's fragile
- JWT_SECRET defaults to `secrets.token_hex(32)` at import time — a new random secret on every restart invalidates all existing tokens. **Must be a stable env var in production.**
- `DEV_MODE=true` effectively bypasses all auth — must be disabled before production deployment.

### Authoritative diagnostics
- `GET /api/auth/me` — first stop for auth debugging; confirms token validity and user identity
- `uv run pytest tests/test_auth.py -v` — targeted auth test suite
- `localStorage.getItem('gymcoach_token')` in browser console — check if token is present

### What assumptions changed
- Original plan assumed all exercises require user_id — seeded exercises are shared so user_id=None was needed
- D011 recorded PyJWT; implementation used python-jose — both are equivalent for HS256
