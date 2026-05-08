# Decisions

<!-- Append-only register of architectural and pattern decisions -->

| ID | Decision | Rationale | Date |
|----|----------|-----------|------|
| D001 | Multi-repo split (backend, frontend, scripts, gsd) | Test GSD subagent parallelism, clean separation | 2026-03-06 |
| D002 | SQLite with WAL mode for v1.0 | Simplicity, local-only, no server needed | 2026-03-06 |
| D003 | FastAPI over Flask | Modern async, auto OpenAPI docs, type hints | 2026-03-06 |
| D004 | Vue 3 over React | User preference, Composition API clean for this scale | 2026-03-06 |
| D005 | Tailwind CSS v4 | Modern utility-first CSS, responsive design straightforward | 2026-03-06 |
| D006 | Naive UTC datetimes in SQLite | Simplicity — caused parsing bugs, fixed with Z suffix normalization | 2026-03-06 |
| D007 | Beanie 2.0 ODM for MongoDB | Native Pydantic v2, uses PyMongo Async (not deprecated Motor) | 2026-03-09 |
| D008 | 4 MongoDB collections (users, exercises, programs, workouts) | 6 SQL tables collapse to document-native schema | 2026-03-09 |
| D009 | Embedded exercises/sets in program documents | Avoids joins, programs change infrequently | 2026-03-09 |
| D010 | Embedded versions array for program versioning | MongoDB document versioning pattern, self-contained | 2026-03-09 |
| D011 | PyJWT for auth tokens | Replaces outdated python-jose, actively maintained | 2026-03-09 |
| D012 | Telegram Login Widget for auth | No password management, zero-friction, HMAC-SHA-256 verification | 2026-03-09 |
| D013 | JWT in localStorage (not httpOnly cookie) | Personal app, threat model doesn't justify CSRF complexity | 2026-03-09 |
| D014 | Dev-mode auth bypass for localhost | Telegram widget requires registered domain via @BotFather | 2026-03-09 |
| D015 | python-jose[cryptography] used for JWT (not PyJWT) | D011 recorded PyJWT as planned; python-jose was chosen at implementation time for easier HMAC+RSA support. Either works; python-jose is pinned in pyproject.toml. | 2026-03-13 |
| D016 | Exercise user_id is nullable (None = shared/seeded) | Shared seed exercises visible to all users; custom exercises owned by one user. Exercises query uses $or filter. | 2026-03-13 |
| D017 | apiFetch utility reads token from localStorage directly | Allows Pinia stores to attach auth headers without needing Vue Router context | 2026-03-13 |
| D018 | nginx/Dockerfile uses parent-dir build context (context: .) | Multi-stage build needs both frontend/ source and nginx/nginx.conf; parent context is the only way to access both in one Dockerfile | 2026-03-13 |
| D019 | Dev compose exposes MongoDB on host port 27018 (not 27017) | Local MongoDB already binds 27017; 27018 avoids conflict without changing internal container networking | 2026-03-13 |
| D020 | Seed + compound index creation in _startup_tasks() called from FastAPI lifespan | Idempotent startup tasks grouped in one place; seed checks count before inserting; indexes use create_index (no-op if exists) | 2026-03-13 |
| D021 | M002 planned as single slice with 3 tasks (not 3 slices) | All three fixes touch the same swipe panel in SetRow→ExerciseCard→ActiveWorkout chain; splitting into slices would mean each touches the same lines; risk is uniformly low (frontend-only, no data changes) | 2026-03-14 |
| D022 | skippedTemplateSets keyed by "exerciseId:setNumber" strings in a Set | Mirrors removedExerciseIds pattern; string keys are simple and hashable; no backend persistence needed since template skips are session-only | 2026-03-14 |
| D023 | M003 decomposed into 3 slices: backend model+seed, i18n+settings UI, exercise wiring+GIF | Natural dependency chain — API fields must exist before frontend can consume them; i18n infrastructure must exist before exercise name switching can be wired; seed upsert is highest risk so goes first | 2026-03-14 |
| D024 | Seed strategy changed from count==0 guard to upsert-by-English-name via Motor bulk_write | Enables adding new exercises and fields to existing DBs without manual collection clear; filters on user_id=None to never touch custom exercises; preserves existing document _ids | 2026-03-14 |
| D025 | vue-i18n v9 with legacy:false for Composition API mode | Reactive locale switching via ref; $t() calls update automatically; standard Vue 3 pattern used by >2M projects | 2026-03-14 |
| D026 | Muscle group translation via static locale file keys, not from API | Muscle groups are a small finite set (6 values); frontend-only translation avoids backend changes; keyed as muscle_groups.Chest = "Грудь" | 2026-03-14 |
| D027 | Settings view added as 5th nav tab with gear icon | No existing Settings surface; language toggle needs a discoverable UI location; gear icon is universally understood | 2026-03-14 |
| D028 | Exercise.id TypeScript type fixed from number to string in M003 | Existing bug — MongoDB uses UUID strings but TS type says number; fixing while touching the type file in M003 is zero marginal cost | 2026-03-14 |
| D029 | useDisplayName composable returns a plain function (not computed) reading settingsStore.language directly | Vue's reactivity tracks settingsStore.language reads inside reactive contexts; plain function avoids per-exercise computed overhead; callable inline in templates as displayName(exercise) | 2026-03-14 |
| D030 | SetRow and workouts store logSet signature fixed from number to string for exercise_id | Cascaded type fix from ExerciseCard emit change; Exercise.id is string but logSet payload was typed as number; fixed in same PR to keep types consistent end-to-end | 2026-03-14 |
