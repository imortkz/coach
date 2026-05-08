---
id: M001
provides:
  - MongoDB/Beanie ODM data layer replacing SQLite/SQLAlchemy across 4 collections
  - Program versioning with embedded ProgramVersion snapshots; workouts reference specific version at log time
  - Telegram Login Widget auth with HMAC-SHA-256 verification and long-lived JWT sessions
  - Multi-user data isolation — user_id on Program, Workout, Setting; nullable on Exercise for shared seeds
  - Dev-mode auth bypass (DEV_MODE=true) for localhost development without Telegram bot
  - Docker Compose stack (nginx + FastAPI + MongoDB) with single docker compose up --build
  - nginx multi-stage build serving Vue SPA and reverse proxying /api/* to backend
  - 50 exercises seeded idempotently at startup; compound indexes created at startup
  - docker-compose.prod.yml and DEPLOYMENT.md for VPS deployment
  - passlib removed, python:3.13-slim base image, scripts/ repo deleted
key_decisions:
  - Beanie 2.0 ODM with PyMongo Async (not Motor) for MongoDB
  - Embedded exercises/sets in program documents; embedded ProgramVersion snapshots in versions array
  - Exercise.user_id nullable (None = shared/seeded, non-null = user-owned) with $or query pattern
  - python-jose[cryptography] for JWT (D011 had planned PyJWT; equivalent for HS256)
  - JWT in localStorage — personal app, CSRF complexity not justified
  - nginx/Dockerfile uses parent-directory build context to access both frontend/ and nginx/ in one multi-stage build
  - Dev compose exposes MongoDB on host port 27018 (not 27017) to avoid conflict with local instance
  - Seed + compound index creation in _startup_tasks() in FastAPI lifespan (idempotent)
  - scripts/ deleted entirely (no archive); analytics/export deferred to future milestone
patterns_established:
  - Beanie Document with string UUID id field and uuid4 default_factory
  - ProgramVersion snapshot appended to versions[] before every PUT update
  - WorkoutSet denormalizes exercise fields (name, muscle_group, equipment) at write time
  - get_current_user FastAPI dependency injected via Depends() on every protected route
  - user_id filter pattern applied to every Find/get call
  - _startup_tasks() in main.py lifespan for idempotent DB setup (seed + indexes)
observability_surfaces:
  - GET /api/health — {"status":"ok","database":"connected"} — first signal for stack health
  - GET /api/auth/me — confirms token validity and user identity
  - docker compose logs backend — seed count, index creation, startup errors
  - docker compose ps — verify all 3 containers running
  - uv run pytest tests/ -q — 59 tests; definitive backend regression signal
requirement_outcomes:
  - id: DB-01
    from_status: active
    to_status: validated
    proof: S07 — 49 passing tests confirm all endpoints work against MongoDB; SQLAlchemy absent from pyproject.toml
  - id: DB-02
    from_status: active
    to_status: validated
    proof: S07 — Exercise CRUD fully tested with Beanie Document model
  - id: DB-03
    from_status: active
    to_status: validated
    proof: S07 — Program create/update with nested ProgramExercise/ProgramSet tested end-to-end
  - id: DB-04
    from_status: active
    to_status: validated
    proof: S07 — WorkoutSet denormalization confirmed in test_log_set
  - id: DB-05
    from_status: active
    to_status: validated
    proof: S07 — All route handlers are async def; no sync SQLAlchemy code remains
  - id: DB-06
    from_status: active
    to_status: validated
    proof: S07 — Tests use gymcoach_test DB; dev DB starts empty; no data migration path
  - id: VER-01
    from_status: active
    to_status: validated
    proof: S07 — test_update_program_replaces_exercises_and_versions confirms current_version increments on PUT
  - id: VER-02
    from_status: active
    to_status: validated
    proof: S07 — Same test confirms versions array grows; ProgramVersion snapshot appended before overwrite
  - id: VER-03
    from_status: active
    to_status: validated
    proof: S07 — test_start_workout confirms workout.program_version captures program.current_version at start time
  - id: VER-04
    from_status: active
    to_status: validated
    proof: S07/S08 — Workout history returns sets with denormalized exercise/version data; user_id filtering in S08
  - id: AUTH-01
    from_status: active
    to_status: validated
    proof: S08 — LoginView.vue renders Telegram widget; route confirmed in npm run build
  - id: AUTH-02
    from_status: active
    to_status: validated
    proof: S08 — verify_telegram_auth() unit tested with correct and incorrect hashes; 401 on bad hash confirmed
  - id: AUTH-03
    from_status: active
    to_status: validated
    proof: S08 — create_access_token() with 365-day expiry; test_jwt_auth_valid_token passes
  - id: AUTH-04
    from_status: active
    to_status: validated
    proof: S08 — POST /api/auth/telegram auto-creates User doc on first login; updates on subsequent logins
  - id: AUTH-05
    from_status: active
    to_status: validated
    proof: S08 — get_current_user dependency on all exercises/programs/workouts/settings routes; test_jwt_auth_invalid_token_returns_401 passes
  - id: AUTH-06
    from_status: active
    to_status: validated
    proof: S08 — DEV_MODE=true skips token requirement; 59 tests pass without auth headers; dev-login endpoint confirmed
  - id: USER-01
    from_status: active
    to_status: validated
    proof: S08 — user_id on Program, Workout, Setting models; Exercise.user_id nullable; confirmed in model definitions
  - id: USER-02
    from_status: active
    to_status: validated
    proof: S08 — All Find/get calls include user_id filter; isolation test confirms user B cannot read user A data (404)
  - id: USER-03
    from_status: active
    to_status: validated
    proof: S09 — Compound indexes (user_id, completed_at) on workouts and (user_id, key) on settings created at startup
  - id: DOCK-01
    from_status: active
    to_status: validated
    proof: S09 — docker compose up --build starts 3 containers; docker compose ps confirms running state
  - id: DOCK-02
    from_status: active
    to_status: validated
    proof: S09 — curl http://localhost/api/health returns connected through nginx; SPA routes return 200
  - id: DOCK-03
    from_status: active
    to_status: validated
    proof: S09 — Named volume mongodb_data persists across docker compose restart; data confirmed after restart
  - id: DOCK-04
    from_status: active
    to_status: validated
    proof: S09 — docker compose up --build from parent dir starts full stack; uv run pytest 59 passed independently
  - id: DOCK-05
    from_status: active
    to_status: validated
    proof: S09 — docker-compose.prod.yml validated via docker compose config; DEV_MODE=false, JWT_SECRET required, MongoDB not exposed
  - id: DOCK-06
    from_status: active
    to_status: validated
    proof: S09 — DEPLOYMENT.md documents BotFather steps, /setdomain for bare IP, VPS checklist
  - id: CLN-01
    from_status: active
    to_status: validated
    proof: S10 — grep passlib backend/pyproject.toml returns no output; SQLAlchemy/Alembic absent since S07
  - id: CLN-02
    from_status: active
    to_status: validated
    proof: S10 — rm -rf ../scripts/ executed; ls ../scripts/ returns "no such directory"; seed data in backend/app/seed.py
duration: ~4 sessions (S07–S10)
verification_result: passed
completed_at: 2026-03-14
---

# M001: GymCoach v1.1 — MongoDB Migration & Deployment

**Replaced SQLite/SQLAlchemy with MongoDB/Beanie across 4 collections, added Telegram auth + JWT + multi-user isolation, and shipped a Docker Compose stack (nginx + FastAPI + MongoDB) deployable with a single command — 59 tests passing, all success criteria met.**

## What Happened

M001 took the v1.0 SQLite MVP and rebuilt the data layer, auth system, and deployment infrastructure in 4 slices.

**S07 — MongoDB Data Layer:** The entire backend was ported from SQLAlchemy/SQLite to Beanie 2.0 ODM. Four collections (exercises, programs, workouts, settings) replaced 6 SQL tables. All 15+ endpoints became `async def`. Program versioning was built in from the start: a `ProgramVersion` snapshot is appended to the `versions[]` array before every PUT update, and `current_version` increments. Workouts capture `program_version` at start time so history is self-contained. WorkoutSet denormalizes exercise fields at write time for the same reason. The 49-test suite was ported to run against real MongoDB.

**S08 — Authentication and Multi-User:** A complete auth layer was added. Backend: Telegram HMAC-SHA-256 verification, JWT issuance (`python-jose`, 365-day expiry), `get_current_user` FastAPI dependency on every protected route, User Beanie document with auto-create on first login. `user_id` was added to Program, Workout, and Setting documents; Exercise uses nullable `user_id` (None = shared seeded, non-null = user-owned) with an `$or` query for list endpoints. Dev mode (`DEV_MODE=true`) bypasses auth entirely so existing tests needed no auth headers — only the conftest needed a `test_user` fixture. Frontend: `auth.ts` store, `apiFetch` utility reading localStorage, `LoginView.vue` with Telegram widget, router guards with dev auto-login. 10 new auth tests brought the suite to 59.

**S09 — Docker Deployment:** A 3-service Docker Compose stack was created at the parent directory level. The nginx container is the key design: a multi-stage Dockerfile (`node:20-slim` builds the Vue SPA with `VITE_TELEGRAM_BOT_NAME` build arg, then `nginx:1.28-alpine` serves it and proxies `/api/*` to the backend). MongoDB 8.0 with a named volume for persistence. Dev compose exposes MongoDB on host port 27018 (not 27017) to avoid conflicts with local instances. `_startup_tasks()` in the FastAPI lifespan seeds 50 exercises (idempotent) and creates compound indexes at every startup. `docker-compose.prod.yml` has `DEV_MODE=false`, no MongoDB port exposure, and requires `JWT_SECRET` from `.env`. `DEPLOYMENT.md` documents the full Telegram bot setup and VPS steps.

**S10 — Cleanup:** `passlib` removed (never imported — Telegram HMAC uses stdlib, JWT uses python-jose). Dockerfile base corrected from `python:3.12-slim` to `python:3.13-slim`. `scripts/` directory deleted entirely — all SQLite-based Alembic migrations and analytics CLI tools gone; seed data lives in `backend/app/seed.py` from S09.

## Cross-Slice Verification

**Success criterion 1: All application data stored in MongoDB with document-native schemas**
- S07: 49 tests pass against real MongoDB using Beanie Document models
- S10: `grep sqlalchemy backend/pyproject.toml` → no output; `grep alembic` → no output

**Success criterion 2: Users authenticate via Telegram Login Widget; data isolated per user**
- S08: `verify_telegram_auth()` unit tested with correct/incorrect hashes; 401 on bad hash confirmed
- S08: User isolation test confirms user B gets 404 for user A's data
- S08: 59 tests pass with `DEV_MODE=true` bypassing auth (backward compatible)

**Success criterion 3: Program versioning preserves history across edits; workouts reference specific versions**
- S07: `test_update_program_replaces_exercises_and_versions` — `current_version` increments, `versions` array grows on each update
- S07: `test_start_workout` — `workout.program_version` field confirms version captured at start time

**Success criterion 4: Docker Compose runs nginx + FastAPI + MongoDB; app accessible in browser**
- S09: `docker compose up --build` → all 3 containers start; MongoDB healthcheck passes; backend reaches "Application startup complete"
- S09: `curl http://localhost/api/health` → `{"status":"ok","database":"connected"}`
- S09: `curl -L http://localhost/api/exercises/` → 50 exercises returned (seed confirmed)
- S09: `curl -I http://localhost/workouts/some-route` → HTTP 200 (SPA fallback confirmed)
- S09: End-to-end: `POST /api/auth/dev-login` + `GET /api/auth/me` with JWT through nginx proxy → dev user returned

**Success criterion 5: Legacy SQLite/SQLAlchemy dependencies removed; scripts repo archived**
- S10: `grep passlib backend/pyproject.toml` → no output
- S10: `ls ../scripts/` → "no such directory"
- S07: SQLAlchemy/Alembic absent from `pyproject.toml` since S07 rewrite

**Definition of done — all slices [x]:** All 10 slices marked complete in M001-ROADMAP.md. Slice summaries exist for S07–S10 (S01–S06 were v1.0 slices without summaries — complete before the GSD artifact convention was established for this project).

## Requirement Changes

- DB-01: active → validated — S07: 49 passing tests confirm all endpoints work against MongoDB
- DB-02: active → validated — S07: Exercise CRUD fully tested
- DB-03: active → validated — S07: Program create/update with nested exercises tested
- DB-04: active → validated — S07: WorkoutSet denormalization confirmed in test_log_set
- DB-05: active → validated — S07: All route handlers are async def
- DB-06: active → validated — S07: Tests use gymcoach_test DB; dev DB starts empty
- VER-01: active → validated — S07: current_version increments on PUT (test confirmed)
- VER-02: active → validated — S07: versions array grows; ProgramVersion snapshot appended before overwrite
- VER-03: active → validated — S07: workout.program_version captured at start time (test confirmed)
- VER-04: active → validated — S07/S08: Workout history returns denormalized data; user-scoped in S08
- AUTH-01: active → validated — S08: LoginView renders Telegram widget; confirmed in build
- AUTH-02: active → validated — S08: HMAC tested with correct/incorrect hashes; 401 on bad hash
- AUTH-03: active → validated — S08: 365-day expiry; test_jwt_auth_valid_token passes
- AUTH-04: active → validated — S08: Auto-create on first Telegram login confirmed
- AUTH-05: active → validated — S08: get_current_user on all protected routes; 401 on invalid token
- AUTH-06: active → validated — S08: DEV_MODE=true bypass; 59 tests pass without auth headers
- USER-01: active → validated — S08: user_id on Program, Workout, Setting; nullable on Exercise
- USER-02: active → validated — S08: All queries filter by user_id; isolation test confirms 404 cross-user
- USER-03: active → validated — S09: Compound indexes on workouts and settings created at startup
- DOCK-01: active → validated — S09: docker compose up starts 3 containers confirmed
- DOCK-02: active → validated — S09: nginx proxies /api/*; SPA routes return 200
- DOCK-03: active → validated — S09: Named volume persists across restart
- DOCK-04: active → validated — S09: Full stack starts; 59 tests pass independently
- DOCK-05: active → validated — S09: docker-compose.prod.yml validated; DEV_MODE=false; MongoDB not exposed
- DOCK-06: active → validated — S09: DEPLOYMENT.md documents BotFather and VPS steps
- CLN-01: active → validated — S10: passlib removed; SQLAlchemy/Alembic absent since S07
- CLN-02: active → validated — S10: scripts/ deleted; seed data in backend/app/seed.py

## Forward Intelligence

### What the next milestone should know
- `JWT_SECRET` defaults to `secrets.token_hex(32)` at import time in `config.py` — generates a new random secret on every restart in dev (intentional for dev safety). Production MUST set a stable `JWT_SECRET` in `.env`.
- `DEV_MODE` defaults to `"true"` — any deployment must explicitly set `DEV_MODE=false` in environment or Docker Compose.
- Telegram auth requires the production domain registered via `@BotFather /setdomain`. Bare IP addresses work if the bot's domain is set to the IP. See DEPLOYMENT.md.
- The `versions[]` array in Program documents grows unbounded — frequent edits to a program will accumulate many snapshots. A `max_versions` cap (keep last N) was not implemented; add it if performance becomes a concern.
- Exercise `user_id=None` is the shared/seed convention. Any future script or tool inserting seed data must leave `user_id` as None. The exercises list endpoint uses `$or: [{user_id: None}, {user_id: current_user.id}]`.
- MongoDB volume is named `mongodb_data` (Docker Compose prefixes with project name, typically `test_gsd_mongodb_data`). On VPS, keep the compose project name consistent to avoid orphaned volumes.

### What's fragile
- `DEV_MODE=true` effectively bypasses all authentication — one misconfigured env var exposes all data. Production deploy must verify `GET /api/auth/me` without a token returns 401.
- `python-jose` is the JWT library (not PyJWT as originally planned in D011). Both work for HS256; D015 documents this deviation. If migrating JWT library, update D015 and `backend/app/auth/jwt.py`.
- Telegram HMAC verification is unit tested but never live-tested end-to-end (requires registered bot + deployed domain). The logic is correct per Telegram docs, but first real login after deployment should be verified manually.

### Authoritative diagnostics
- `GET /api/health` — first signal for MongoDB connectivity through nginx
- `GET /api/auth/me` — confirms auth state; 401 means token invalid or missing, 200 means auth working
- `docker compose logs backend` — seed count, index creation, startup errors
- `uv run pytest tests/ -q` in `../backend/` — 59 tests; any failure is a regression

### What assumptions changed
- D011 recorded PyJWT as planned; python-jose was used at implementation time (D015). Both are equivalent.
- Original schema planned 4 collections including `users`; `settings` collection was added for progression increment overrides (pre-existing from v1.0 rewrite).
- Exercise user_id was originally required — changed to nullable to support shared seed exercises.
- nginx/Dockerfile originally expected to reuse the frontend Dockerfile as a pure builder; cleaner to create a new nginx/Dockerfile with parent-dir build context.

## Files Created/Modified

- `../backend/app/database.py` — Beanie init with AsyncMongoClient, document model registration including User
- `../backend/app/config.py` — MongoDB, JWT, Telegram, DEV_MODE config from env
- `../backend/app/main.py` — FastAPI lifespan with _startup_tasks (seed + indexes), all routers, CORS
- `../backend/app/seed.py` — 50 exercises, idempotent async seed (checks count before inserting)
- `../backend/app/auth/__init__.py` — auth module
- `../backend/app/auth/models.py` — User Beanie document
- `../backend/app/auth/jwt.py` — JWT create/decode (python-jose, HS256, 365-day expiry)
- `../backend/app/auth/telegram.py` — HMAC-SHA-256 Telegram login verification
- `../backend/app/auth/dependencies.py` — get_current_user with dev bypass
- `../backend/app/auth/routes.py` — POST /api/auth/telegram, POST /api/auth/dev-login
- `../backend/app/exercises/models.py` — Exercise Beanie Document with nullable user_id
- `../backend/app/exercises/routes.py` — async CRUD + history; $or query for shared+owned; auth dependency
- `../backend/app/programs/models.py` — Program, ProgramExercise, ProgramSet, ProgramVersion with user_id
- `../backend/app/programs/routes.py` — async CRUD with versioning; user_id filter; auth dependency
- `../backend/app/workouts/models.py` — Workout, WorkoutSet, Setting with user_id; compound indexes
- `../backend/app/workouts/routes.py` — async workout logging, settings, progression; user_id filter; auth dependency
- `../backend/pyproject.toml` — beanie, python-jose, fastapi, uvicorn, pydantic; passlib removed
- `../backend/Dockerfile` — python:3.13-slim base image
- `../backend/tests/conftest.py` — test_user fixture, follow_redirects=True, User in init_beanie
- `../backend/tests/test_auth.py` — 10 auth tests
- `../backend/tests/test_workouts.py` — updated for user_id
- `../backend/tests/test_exercises.py` — updated for user_id
- `../frontend/src/stores/auth.ts` — token persistence, devLogin, telegramLogin, fetchMe
- `../frontend/src/lib/apiFetch.ts` — authenticated fetch from localStorage
- `../frontend/src/composables/useApi.ts` — Vue-context auth fetch
- `../frontend/src/views/LoginView.vue` — Telegram widget + dev mode button
- `../frontend/src/router/index.ts` — /login route + beforeEach guard with dev auto-login
- `../docker-compose.yml` — 3-service dev stack, DEV_MODE=true, MongoDB port 27018
- `../docker-compose.prod.yml` — 3-service production stack, DEV_MODE=false, required env vars
- `../nginx/Dockerfile` — multi-stage: node build + nginx:1.28-alpine
- `../nginx/nginx.conf` — /api/* proxy to backend:8000, try_files SPA fallback
- `../.env.example` — JWT_SECRET, TELEGRAM_BOT_TOKEN, VITE_TELEGRAM_BOT_NAME with guidance
- `../DEPLOYMENT.md` — Telegram bot setup, VPS deployment, backup/restore, troubleshooting
- `../scripts/` — deleted entirely
