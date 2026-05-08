# Requirements

## Active





## Validated

### CLN-01 — SQLAlchemy and Alembic dependencies removed from backend
- Status: validated
- Validated in: S10 — pyproject.toml verified clean (absent since S07); passlib also removed

### CLN-02 — Scripts repo archived (analytics/export deferred to future milestone)
- Status: validated
- Validated in: S10 — scripts/ directory deleted from disk; seed data in backend/app/seed.py; analytics/export deferred

### USER-03 — Compound indexes include user_id as prefix for query performance
- Status: validated
- Validated in: S09 — Compound indexes (user_id, completed_at) on workouts and (user_id, key) on settings created at backend startup; confirmed in MongoDB logs

### DOCK-01 — docker-compose.yml defines 3 services: nginx, backend, mongodb
- Status: validated
- Validated in: S09 — docker compose up --build starts all 3 containers; docker compose ps confirms running state

### DOCK-02 — nginx serves built Vue SPA and reverse proxies /api/* to backend
- Status: validated
- Validated in: S09 — curl http://localhost/api/health returns connected; curl http://localhost/ returns 200 HTML; deep SPA routes return 200

### DOCK-03 — MongoDB data persists via Docker volume
- Status: validated
- Validated in: S09 — Named volume mongodb_data persists across docker compose restart; data confirmed after restart

### DOCK-04 — Automated dev pipeline: docker-compose build + up + run tests
- Status: validated
- Validated in: S09 — docker compose up --build from parent dir starts full stack; uv run pytest 59 passed independently

### DOCK-05 — Production docker-compose and nginx config for VPS deployment with bare IP
- Status: validated
- Validated in: S09 — docker-compose.prod.yml validated via docker compose config; DEV_MODE=false, JWT_SECRET required, MongoDB not exposed

### DOCK-06 — Telegram bot setup documented as deployment prerequisite
- Status: validated
- Validated in: S09 — DEPLOYMENT.md documents BotFather steps, /setdomain for bare IP, VPS checklist

### DB-01 — All data storage uses MongoDB with Beanie ODM instead of SQLite/SQLAlchemy
- Status: validated
- Validated in: S07 — 49 passing tests confirm all endpoints work against MongoDB

### DB-02 — Exercises stored as a shared collection with document-native schema
- Status: validated
- Validated in: S07 — Exercise CRUD fully tested

### DB-03 — Programs stored as documents with embedded exercises and sets
- Status: validated
- Validated in: S07 — Program create/update with nested exercises tested end-to-end

### DB-04 — Workouts stored as self-contained documents with full exercise/set data denormalized at write time
- Status: validated
- Validated in: S07 — WorkoutSet denormalization confirmed in test_log_set

### DB-05 — All backend endpoints converted from sync def to async def
- Status: validated
- Validated in: S07 — All route handlers are async def; no sync SQLAlchemy code remains

### DB-06 — Existing v1.0 test data dropped (clean start with MongoDB)
- Status: validated
- Validated in: S07 — Tests use gymcoach_test DB; dev DB starts empty

### VER-01 — Program document includes version tracking (version number increments on edit)
- Status: validated
- Validated in: S07 — test_update_program_replaces_exercises_and_versions confirms version increment

### VER-02 — When a program is edited, previous version snapshot is preserved
- Status: validated
- Validated in: S07 — Same test confirms versions array grows on each update

### VER-03 — Workout documents reference the specific program version they were logged against
- Status: validated
- Validated in: S07 — test_start_workout confirms program_version stored on workout document

### VER-04 — User can view workout history with the correct program version context
- Status: validated
- Validated in: S07, S08 — Workout history returns sets with denormalized exercise/version data; user_id filtering confirmed in S08

### AUTH-01 — User can authenticate via Telegram Login Widget on the login page
- Status: validated
- Validated in: S08 — LoginView renders Telegram widget; HMAC verified in backend; JWT issued

### AUTH-02 — Backend verifies Telegram login using HMAC-SHA-256 with bot token
- Status: validated
- Validated in: S08 — verify_telegram_auth() tested with correct/incorrect hashes; returns 401 on bad hash

### AUTH-03 — Authenticated user receives a JWT session token valid for 1 year
- Status: validated
- Validated in: S08 — create_access_token() with 365-day expiry; test_jwt_auth_valid_token passes

### AUTH-04 — User account is auto-created on first Telegram login with name/username from Telegram
- Status: validated
- Validated in: S08 — POST /api/auth/telegram creates User doc if telegram_id not found; updates on subsequent logins

### AUTH-05 — All API endpoints except auth and health require valid JWT Bearer token
- Status: validated
- Validated in: S08 — get_current_user dependency on all exercises/programs/workouts/settings routes; test_jwt_auth_invalid_token_returns_401 passes

### AUTH-06 — Dev-mode auth bypass available for localhost development without Telegram bot
- Status: validated
- Validated in: S08 — DEV_MODE=true skips token requirement; POST /api/auth/dev-login endpoint; router guard auto-logins in dev; 59 tests pass without auth headers

### USER-01 — Every document (exercise, program, workout) has a user_id field
- Status: validated
- Validated in: S08 — user_id on Program, Workout, Setting models; Exercise.user_id nullable (None = shared seed)

### USER-02 — Every query filters by the authenticated user's ID
- Status: validated
- Validated in: S08 — All Find/get calls include user_id filter; isolation test confirms user B cannot read user A's data

### MVP-01 — Create and manage exercise lists with sets/reps/weight targets
- Status: validated
- Validated in: S01, S02 (v1.0)

### MVP-02 — Log completed sets with actual weight and reps during a workout
- Status: validated
- Validated in: S03 (v1.0)

### MVP-03 — Auto-suggest weight increases based on logged performance
- Status: validated
- Validated in: S04 (v1.0)

### MVP-04 — View workout history and progress
- Status: validated
- Validated in: S04 (v1.0)

### MVP-05 — Mobile-friendly web UI for use at the gym
- Status: validated
- Validated in: S03, S06 (v1.0)

### MVP-06 — SQLite storage for all data
- Status: validated
- Validated in: S01 (v1.0)
- Note: Superseded by DB-01 (MongoDB). SQLite removed in S07.
- Note: Will be superseded by DB-01 (MongoDB migration)

### MVP-07 — DB schema migrations and seed data
- Status: validated
- Validated in: S01 (v1.0)

### MVP-08 — CLI analytics scripts for progress reports
- Status: validated
- Validated in: S05 (v1.0)
- Note: Will be deferred/archived per CLN-02

## Deferred

## Out of Scope
