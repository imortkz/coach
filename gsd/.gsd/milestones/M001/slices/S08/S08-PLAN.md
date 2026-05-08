# S08: Authentication and Multi-User

**Goal:** Telegram Login Widget authentication with JWT sessions, user-scoped data isolation on all documents, dev-mode auth bypass.
**Demo:** User authenticates via Telegram widget, gets a JWT, all data is scoped to their user_id, dev mode works without Telegram bot.

## Must-Haves
- Telegram Login Widget rendered on /login page with HMAC-SHA-256 verification on backend
- JWT issued on successful auth (1-year expiry), auto-create user on first login
- get_current_user FastAPI dependency on all protected endpoints
- Every MongoDB query filters by authenticated user's user_id
- Dev-mode auth bypass works on localhost without Telegram bot

## Tasks
TBD — pending slice planning

## Files Likely Touched
- backend/app/auth/ (new module: routes, dependencies, telegram verification, JWT)
- frontend/src/views/LoginView.vue (new)
- frontend/src/stores/auth.ts (new)
- frontend/src/composables/useApi.ts (new)
- frontend/src/router/index.ts (auth guards)
