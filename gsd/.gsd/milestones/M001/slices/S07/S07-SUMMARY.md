---
id: S07
parent: M001
milestone: M001
provides:
  - MongoDB/Beanie ODM data layer replacing SQLite/SQLAlchemy
  - Async FastAPI endpoints for exercises, programs, workouts, settings
  - Program versioning with embedded ProgramVersion snapshots
  - Workout documents capturing program_version at log time
  - 49-test pytest suite against real MongoDB
requires:
  - slice: S06
    provides: v1.0 MVP with SQLite backend, polished frontend
affects:
  - S08
  - S09
  - S10
key_files:
  - backend/app/database.py
  - backend/app/exercises/models.py
  - backend/app/exercises/routes.py
  - backend/app/exercises/schemas.py
  - backend/app/programs/models.py
  - backend/app/programs/routes.py
  - backend/app/programs/schemas.py
  - backend/app/workouts/models.py
  - backend/app/workouts/routes.py
  - backend/app/workouts/schemas.py
  - backend/app/main.py
  - backend/app/config.py
  - backend/tests/conftest.py
  - backend/pyproject.toml
key_decisions:
  - Beanie 2.0 ODM with PyMongo Async (not Motor) for MongoDB
  - 4 collections: exercises, programs, workouts, settings
  - Embedded exercises/sets inside program documents (no joins)
  - Embedded versions array in program document for version history
  - String UUIDs for document IDs (not ObjectId) for API compatibility
  - workout.program_version captures current_version at workout start time
patterns_established:
  - Beanie Document model with str ID and uuid4 default_factory
  - ProgramVersion embedded snapshot appended before each PUT update
  - Denormalized exercise fields (name, muscle_group, equipment) in WorkoutSet
  - pre_fill computed from last completed workout or program template fallback
  - compute_progression(): equipment-specific weight increment with Setting override
observability_surfaces:
  - GET /api/health returns {"status":"ok","database":"connected"|"disconnected"}
drill_down_paths: []
duration: ~1 session
verification_result: passed
completed_at: 2026-03-13
---

# S07: MongoDB Data Layer

**Replaced SQLite/SQLAlchemy with MongoDB/Beanie ODM across all 4 collections; all 15+ endpoints are async; program versioning archives previous state on every PUT; workouts capture program_version at log time. 49 tests pass.**

## What Happened

The backend was fully migrated from SQLite/SQLAlchemy to MongoDB with the Beanie 2.0 ODM. All four collections (exercises, programs, workouts, settings) were defined as Beanie `Document` subclasses with UUID string IDs. Every route handler was rewritten as `async def`. The `database.py` module initializes Beanie via `init_beanie()` in the FastAPI lifespan.

**Program versioning** was implemented by appending a `ProgramVersion` snapshot (containing the current name, rest_timer_disabled flag, and full exercises/sets list) to `program.versions` before any PUT overwrite. The `current_version` counter increments on each save. Workout documents record `program_version` equal to the program's `current_version` at the moment the workout is started.

**Exercise data** is denormalized into both `ProgramExercise` (for clean program snapshots) and `WorkoutSet` (so completed workout history is self-contained and never corrupted by later exercise renames/deletions).

**Pre-fill and progression logic** was ported: pre-fill looks up the last completed workout per exercise and falls back to program template targets; progression uses equipment-specific kg increments with per-equipment Setting overrides.

The test suite (49 tests across 4 files) was inherited from the v1.0 rewrite. Two issues were fixed to make all tests pass:
1. FastAPI 307-redirects on routes defined with `"/"` path caused tests using `/api/exercises` (no trailing slash) to fail — fixed by adding `follow_redirects=True` to the httpx `AsyncClient` in conftest.
2. The health check test failed because the test client bypasses the FastAPI lifespan (so `database.client` was None) — fixed by exposing the MongoClient on the `app.database` module from the `db` fixture.

## Verification

- `uv run pytest tests/ -v` → **49 passed, 0 failed**
- `GET /api/health` → `{"status":"ok","database":"connected"}` (live server)
- Exercises CRUD: list with filters (muscle_group, equipment, search), create, update, delete (403 for seeded, 409 if in-use)
- Programs CRUD: create with nested exercises+sets, list, get, update (versions archived), delete
- Workouts: start (with pre-fill + progression suggestions), log sets, update set, delete set, complete, discard, list with pagination
- Settings CRUD (upsert pattern for progression increment overrides)
- Exercise history endpoint returns sessions + progression suggestion

## Requirements Advanced

- DB-01 — All data storage uses MongoDB with Beanie ODM (fully replaced SQLite/SQLAlchemy)
- DB-02 — Exercises stored as shared collection `exercises` with document-native schema
- DB-03 — Programs stored with embedded exercises and sets (ProgramExercise + ProgramSet)
- DB-04 — Workouts stored as self-contained documents; WorkoutSet denormalizes exercise fields at write time
- DB-05 — All backend endpoints converted to `async def`
- DB-06 — Clean MongoDB start (no legacy SQLite data migrated)
- VER-01 — Program.current_version increments on every PUT
- VER-02 — ProgramVersion snapshot appended to Program.versions before each PUT
- VER-03 — Workout.program_version captures program.current_version at workout start
- VER-04 — Workout history returns sets with denormalized exercise data; version context preserved in workout document

## Requirements Validated

- DB-01 — 49 passing tests confirm all endpoints work against MongoDB
- DB-02 — Exercise CRUD fully tested
- DB-03 — Program create/update with nested exercises tested end-to-end
- DB-04 — WorkoutSet denormalization confirmed in test_log_set
- DB-05 — All route handlers are async def; no sync SQLAlchemy code remains
- VER-01 — test_update_program_replaces_exercises_and_versions confirms version increment
- VER-02 — Same test confirms versions array grows on each update
- VER-03 — test_start_workout confirms program_version stored on workout document

## New Requirements Surfaced

- none

## Requirements Invalidated or Re-scoped

- MVP-06 (SQLite storage) — superseded by DB-01 (MongoDB). Moving to Validated with note.

## Deviations

- `Setting` collection added beyond the 4 originally listed (users, exercises, programs, workouts) to support per-equipment progression increment overrides. This was a pre-existing design from the v1.0 rewrite carried forward unchanged.
- `user_id` field is NOT yet on documents — deferred to S08 per original plan. USER-01/02/03 remain Active.

## Known Limitations

- No `user_id` on any document yet; all data is shared across all (currently single) users. S08 adds auth and user isolation.
- The 307 redirect on `/api/exercises` (no trailing slash) will be followed by browsers and httpx but could confuse simple curl invocations. Routes could be changed to `""` paths, but this is low priority.
- `mongo_client.close()` in conftest uses `aclose()` (async) — pymongo's async close API may change across versions.

## Follow-ups

- S08: Add `user_id` to all four collections and filter all queries by authenticated user
- S08: Implement Telegram Login Widget + HMAC verification + JWT issuance
- S09: Docker Compose with MongoDB service, nginx, and backend container
- S10: Remove any remaining SQLAlchemy/Alembic references (pyproject.toml is already clean)

## Files Created/Modified

- `backend/app/database.py` — Beanie init with AsyncMongoClient, 4 document models
- `backend/app/config.py` — MONGODB_URL and MONGODB_DB_NAME from env
- `backend/app/main.py` — FastAPI app with lifespan, CORS, 4 routers
- `backend/app/exercises/models.py` — Exercise Beanie Document
- `backend/app/exercises/routes.py` — Async exercise CRUD + history endpoint
- `backend/app/exercises/schemas.py` — ExerciseRead/Create/Update Pydantic models
- `backend/app/programs/models.py` — Program, ProgramExercise, ProgramSet, ProgramVersion
- `backend/app/programs/routes.py` — Async program CRUD with versioning
- `backend/app/programs/schemas.py` — ProgramRead/Create/Update with nested schemas
- `backend/app/workouts/models.py` — Workout, WorkoutSet, Setting Beanie Documents
- `backend/app/workouts/routes.py` — Async workout logging, settings, progression logic
- `backend/app/workouts/schemas.py` — Full workout/set/settings schema suite
- `backend/pyproject.toml` — beanie, fastapi, uvicorn, pydantic; no SQLAlchemy/Alembic
- `backend/pytest.ini` — asyncio_mode = auto
- `backend/tests/conftest.py` — Fixed: follow_redirects=True, db fixture exposes client to health check
- `backend/Dockerfile` — Container for S09 deployment

## Forward Intelligence

### What the next slice should know
- All documents use string UUIDs as `id` (not MongoDB ObjectId). The `_id` field in MongoDB is also the UUID string. Beanie handles this via the `id` field alias.
- `user_id` field needs to be added to Exercise, Program, Workout, Setting models in S08. Add as `Optional[str]` first, then add index and make required after data migration.
- The `versions` array in Program can grow large for frequently-edited programs — consider a `max_versions` cap in S08 or later.
- The lifespan pattern in `main.py` calls `init_db()` at startup. S08's auth middleware should also be registered in `main.py`.
- Dev-mode auth bypass (AUTH-06) should check `GYMCOACH_DEV_MODE=true` env var and inject a hardcoded test user_id so existing tests continue to pass without Telegram credentials.

### What's fragile
- `Exercise.get(exercise_id)` returns None silently if the ID doesn't exist (Beanie behavior) — routes handle this with 404, but callers that don't check (e.g., denormalization in program/workout creation) will silently produce empty strings for exercise_name etc.
- `conftest.py db fixture` drops all collections after each test — if a test creates data in a shared session, ordering matters. Currently all tests are isolated via the per-test `db` fixture.

### Authoritative diagnostics
- `GET /api/health` — first signal for MongoDB connectivity issues
- `uv run pytest tests/ -v` — definitive test suite; all 49 must pass before S08 work begins
- `uv run uvicorn app.main:app --reload` in `../backend/` — live dev server

### What assumptions changed
- Original plan listed 4 collections (users, exercises, programs, workouts) — `users` collection is deferred to S08; `settings` collection was added in the v1.0→S07 rewrite for progression increment overrides.
- Tests run against a real MongoDB instance (localhost:27017), not mongomock — simpler and more realistic, but requires MongoDB to be running in CI/Docker.
