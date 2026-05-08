# S07: MongoDB Data Layer — UAT

**Milestone:** M001
**Written:** 2026-03-13

## UAT Type

- UAT mode: live-runtime
- Why this mode is sufficient: All 49 pytest tests run against a real MongoDB instance and exercise every endpoint contract. Automated tests cover CRUD, filters, versioning, progression, and pre-fill logic — the full slice scope.

## Preconditions

- MongoDB running at `localhost:27017` (or `MONGODB_URL` env var set)
- Backend started: `cd ../backend && uv run uvicorn app.main:app --reload`
- Optionally seed exercises: POST a few exercises via `/api/exercises`
- Test suite passes: `uv run pytest tests/ -v` → 49 passed

## Smoke Test

```
curl http://localhost:8000/api/health
# Expected: {"status":"ok","database":"connected"}
```

## Test Cases

### 1. Exercise CRUD

1. `GET /api/exercises` → `[]` (empty on fresh DB)
2. `POST /api/exercises` with `{"name":"Bench Press","muscle_group":"Chest","equipment":"Barbell"}` → 201, `is_custom: true`
3. `GET /api/exercises?muscle_group=Chest` → array with one exercise
4. `GET /api/exercises?search=bench` → case-insensitive match
5. `PUT /api/exercises/{id}` update name → 200 with updated name
6. `DELETE /api/exercises/{id}` → 204
7. **Expected:** All operations return correct data; seeded exercises (is_custom=false) reject PUT/DELETE with 403

### 2. Program Create and Versioning

1. Create an exercise (POST `/api/exercises`)
2. `POST /api/programs` with nested exercises and per-set targets → 201, `current_version: 1`
3. `PUT /api/programs/{id}` with different exercises → 200, `current_version: 2`
4. Repeat PUT → `current_version: 3`
5. **Expected:** Each PUT increments `current_version`; previous state is stored in `versions` array (verifiable via MongoDB shell: `db.programs.findOne().versions`)

### 3. Workout Lifecycle with Pre-fill and Progression

1. Create a program with 3x8 Bench Press @ 80kg target
2. Start workout: `POST /api/workouts` with `program_id` → 201, includes `pre_fill` and empty `suggestions` (no history yet)
3. Log sets: `POST /api/workouts/{id}/sets` for each set with weight_kg=80, reps=8
4. Complete workout: `PATCH /api/workouts/{id}/complete` → 200 with `completed_at`
5. Start second workout → `pre_fill` shows 80kg/8 from last session; `suggestions` shows `type: "weight", suggested_weight_kg: 82.5`
6. `GET /api/workouts` → paginated list of completed workouts
7. **Expected:** Pre-fill reflects last session; progression suggests +2.5kg after hitting all target reps

### 4. Exercise History

1. After completing workout with Bench Press:
2. `GET /api/exercises/{id}/history` → sessions array with one entry
3. `GET /api/exercises/{id}/history?program_id={pid}` → includes `suggestion` object
4. **Expected:** Session shows correct date, sets, best_weight, total_volume

### 5. Settings (Progression Increment Override)

1. `PUT /api/settings/progression_increment_barbell` with `{"value": "5.0"}` → 201/200
2. `GET /api/settings/progression_increment_barbell` → `{"key":"...","value":"5.0"}`
3. Complete a Barbell workout hitting all targets → suggestion shows +5kg increment
4. **Expected:** Custom increment overrides default 2.5kg for Barbell

### 6. Workout Discards and Set Management

1. Start workout, log a set, then `DELETE /api/workouts/{id}` → 204
2. Start another workout, log sets, `DELETE /api/workouts/{id}/sets/{set_id}` → 204
3. `DELETE /api/workouts/{id}/exercises/{exercise_id}` → removes all sets for that exercise
4. **Expected:** Discarded workout gone from active; set deletions remove correct embedded documents

## Edge Cases

### Workout program_version captured at start

1. Create program (version=1), start workout → check workout.program_version=1 in DB
2. Update program (version=2)
3. Check existing workout still has program_version=1
4. **Expected:** Version snapshot is immutable after workout creation

### Exercise delete blocked by program usage

1. Create exercise, add to program
2. `DELETE /api/exercises/{id}` → 409 with message listing the program
3. **Expected:** Exercise remains; error message names the blocking program

### Empty exercise list on fresh DB

1. `GET /api/exercises` → `[]` (not 500)
2. `GET /api/programs` → `[]`
3. `GET /api/workouts` → `{"items":[]}`
4. **Expected:** All empty-list endpoints return valid JSON, not errors

## Failure Signals

- Any 500 response indicates a MongoDB query error — check uvicorn logs
- `"database":"disconnected"` from health check means MongoDB is unreachable
- 307 redirect from exercises/programs without `follow_redirects` in client — expected behavior, not a bug
- Empty `suggestion` when history exists — check that `completed_at` is not null on the workout

## Requirements Proved By This UAT

- DB-01 — All data in MongoDB, no SQLite files created
- DB-02 — Exercise collection CRUD verified
- DB-03 — Program with embedded exercises and sets round-trips correctly
- DB-04 — WorkoutSet contains denormalized exercise fields (visible in workout response)
- DB-05 — All handlers are async; no blocking I/O observed
- VER-01 — current_version increments on program PUT
- VER-02 — versions array grows on program PUT (verifiable in DB)
- VER-03 — workout.program_version captured at start time
- VER-04 — workout history shows correct exercise data from denormalized snapshot

## Not Proven By This UAT

- USER-01/02/03 — user_id isolation not tested (deferred to S08)
- AUTH-01 through AUTH-06 — no authentication implemented yet (S08)
- DOCK-01 through DOCK-06 — no Docker deployment (S09)
- CLN-01/CLN-02 — SQLAlchemy still absent from pyproject.toml, but scripts repo not archived yet (S10)

## Notes for Tester

- The `versions` array is not exposed in the API response (`ProgramRead` schema doesn't include it). To inspect version history, use a MongoDB client: `db.programs.findOne({}, {versions:1})`
- The test database is `gymcoach_test` — the dev database is `gymcoach`. Tests clean up after themselves.
- MongoDB must be running locally; there is no mongomock fallback. Start MongoDB before running tests.
- `uv run pytest tests/ -v` is the authoritative verification — browser/curl testing is optional smoke testing on top.
