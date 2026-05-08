# S08: Authentication and Multi-User — UAT

**Milestone:** M001
**Written:** 2026-03-13

## UAT Type

- UAT mode: artifact-driven (tests) + live-runtime (backend server) + human-experience (browser login flow)
- Why this mode is sufficient: Backend auth logic fully covered by automated tests (59 passing). Frontend login flow and Telegram widget are verified via build + manual navigation. Telegram HMAC end-to-end requires a live bot — documented as known gap.

## Preconditions

- MongoDB running locally (`mongodb://localhost:27017`)
- Backend: `cd ../backend && uv run uvicorn app.main:app --reload`
- Frontend: `cd ../frontend && npm run dev`
- `DEV_MODE=true` (default) — no Telegram bot needed for dev UAT
- For Telegram UAT: Set `TELEGRAM_BOT_TOKEN` and `VITE_TELEGRAM_BOT_NAME` env vars

## Smoke Test

Run `cd ../backend && uv run pytest tests/ -q` — all 59 tests must pass. Then navigate to http://localhost:5173 — should redirect to `/login` or auto-login in dev mode.

## Test Cases

### 1. Dev mode auto-login (no token)

1. Clear localStorage in browser (`localStorage.clear()`)
2. Navigate to http://localhost:5173/exercises
3. **Expected:** Router guard calls `/api/auth/dev-login`, gets a JWT, stores it, and the exercises page loads without seeing the login screen

### 2. Dev login endpoint

1. `curl -X POST http://localhost:8000/api/auth/dev-login`
2. **Expected:** 200 response with `access_token`, `token_type: "bearer"`, `user_id: "dev-user-000"`, `first_name`

### 3. JWT auth — valid token

1. Get token from dev-login above
2. `curl -H "Authorization: Bearer <token>" http://localhost:8000/api/auth/me`
3. **Expected:** 200 with user JSON containing `id`, `first_name`, `telegram_id`

### 4. JWT auth — invalid token

1. `curl -H "Authorization: Bearer bad.token.here" http://localhost:8000/api/exercises/`
2. **Expected:** 401 with `{"detail": "Invalid or expired token"}`

### 5. No token in production-like mode (DEV_MODE=false)

1. Set `DEV_MODE=false` and restart backend
2. `curl http://localhost:8000/api/exercises/`
3. **Expected:** 401 (no Bearer token provided)

### 6. Data isolation — programs

1. Create two users (user A via dev-login, user B via separate JWT)
2. Create a program as user A
3. List programs as user B
4. **Expected:** User B's program list does not include user A's program; `GET /api/programs/<user_a_program_id>` with user B token returns 404

### 7. Data isolation — workouts

1. Start workout as user A
2. `GET /api/workouts/active` with user B token
3. **Expected:** 404 — user B has no active workout

### 8. Login page — dev mode button

1. Navigate to http://localhost:5173/login
2. **Expected:** "Continue as Dev User" button visible; clicking it logs in and redirects to /exercises

### 9. Login page — Telegram widget (requires bot)

1. Set `VITE_TELEGRAM_BOT_NAME=<your_bot>` and rebuild frontend
2. Navigate to http://localhost:5173/login
3. **Expected:** Telegram Login Widget renders with bot name; clicking authenticates and redirects

### 10. Telegram HMAC rejection

1. `POST /api/auth/telegram` with valid structure but wrong `hash`
2. **Expected:** 401 `{"detail": "Invalid Telegram authentication data"}`

### 11. /api/health still public

1. `curl http://localhost:8000/api/health` (no token)
2. **Expected:** 200 `{"status": "ok", ...}` — health check never requires auth

## Edge Cases

### Missing Telegram bot token

1. Set `TELEGRAM_BOT_TOKEN=""` and restart backend
2. `POST /api/auth/telegram` with any data
3. **Expected:** 503 `{"detail": "Telegram bot token not configured"}`

### Expired/tampered JWT

1. Create a JWT, tamper with the payload
2. Use as Bearer token
3. **Expected:** 401

### Custom exercise owned by other user

1. User A creates a custom exercise
2. User B tries to PUT or DELETE it
3. **Expected:** 403 for modify/delete; exercise visible in list (shared seeded are visible; custom are not visible to B)
4. **Note:** Custom exercises with user_id set to user A are NOT in user B's list

## Failure Signals

- Any route returning 500 on valid auth request — check logs for missing `user_id` on document insert
- `GET /api/exercises/` returns 401 even in dev mode — check `DEV_MODE` env var
- Frontend shows login page on every refresh in dev mode — `localStorage.getItem('gymcoach_token')` should be set
- `JWT_SECRET` not set in production → tokens will be invalidated on every restart

## Requirements Proved By This UAT

- AUTH-01 — Telegram widget renders on /login page (manual browser check)
- AUTH-02 — HMAC verification tested: wrong hash → 401 (test_auth.py + manual curl)
- AUTH-03 — JWT issued on dev-login; token decoded in test_jwt_auth_valid_token
- AUTH-04 — User auto-created on dev-login; updated fields on re-login (test_dev_login_endpoint)
- AUTH-05 — Invalid token → 401 on exercises route (test_jwt_auth_invalid_token_returns_401)
- AUTH-06 — 59 tests run without auth headers with DEV_MODE=true
- USER-01 — user_id present on Program, Workout, Setting documents (model definitions)
- USER-02 — User B cannot read user A's programs/workouts (test_user_b_cannot_see_user_a_programs)

## Not Proven By This UAT

- Telegram Login Widget end-to-end flow with a live registered bot (requires deployed domain + @BotFather config)
- JWT expiry actually expires after 1 year (time-based, not test-verified)
- USER-03 compound indexes performance under load (deferred to S09)
- Frontend LoginView renders correctly on mobile (not checked in this slice)

## Notes for Tester

- `DEV_MODE` defaults to `true` — you will always be auto-logged in locally unless you explicitly pass a bad token
- The dev user ID is `dev-user-000` (configurable via `DEV_USER_ID` env var)
- `JWT_SECRET` must be set to a stable value in `.env` or Docker compose for tokens to survive restarts
- Telegram widget will silently not render if `VITE_TELEGRAM_BOT_NAME` is not set — this is expected in dev
- Custom exercises (is_custom=True) are user-scoped; seeded exercises (user_id=None) are shared across all users
