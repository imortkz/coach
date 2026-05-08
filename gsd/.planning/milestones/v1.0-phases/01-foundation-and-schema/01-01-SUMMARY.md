---
phase: 01-foundation-and-schema
plan: 01
subsystem: database
tags: [sqlalchemy, alembic, sqlite, click, uv]

# Dependency graph
requires: []
provides:
  - SQLAlchemy 2.0 models for all 6 tables (Exercise, Program, ProgramExercise, Workout, WorkoutSet, Setting)
  - Alembic migration infrastructure with render_as_batch for SQLite
  - Exercise seed data (50 exercises across 6 muscle groups)
  - CLI entry point (python -m gymcoach_scripts migrate/seed)
affects: [01-02, 01-03, 02-exercise-and-program-management]

# Tech tracking
tech-stack:
  added: [sqlalchemy 2.0.48, alembic 1.18.4, click 8.3.1, rich 14.3.3, python-dotenv 1.2.2, ruff 0.15.5, pytest 9.0.2, hatchling]
  patterns: [SQLAlchemy 2.0 Mapped[] declarative style, WAL mode + foreign keys via connect event, render_as_batch for SQLite migrations]

key-files:
  created:
    - ../scripts/gymcoach_scripts/db/models.py
    - ../scripts/gymcoach_scripts/db/engine.py
    - ../scripts/gymcoach_scripts/db/alembic/env.py
    - ../scripts/gymcoach_scripts/seed.py
    - ../scripts/gymcoach_scripts/seed_data/exercises.json
    - ../scripts/gymcoach_scripts/cli.py
    - ../scripts/gymcoach_scripts/__main__.py
    - ../scripts/gymcoach_scripts/migrate.py
    - ../scripts/tests/test_migrations.py
    - ../scripts/tests/test_seed.py
  modified: []

key-decisions:
  - "Used hatchling build backend so gymcoach_scripts is installable as a package"
  - "Alembic env.py reads GYMCOACH_DB env var at call time (not import time) for test isolation"

patterns-established:
  - "SQLAlchemy 2.0 Mapped[] style for all models"
  - "WAL mode and foreign keys enforced via engine connect event listener"
  - "Alembic render_as_batch=True for SQLite ALTER TABLE compatibility"
  - "Seed data stored as JSON in seed_data/ directory"

requirements-completed: [SCRP-01, SCRP-02]

# Metrics
duration: 5min
completed: 2026-03-06
---

# Phase 1 Plan 01: Scripts Repo Summary

**SQLAlchemy 2.0 models for 6 tables with Alembic migrations, 50-exercise seed data, and Click CLI**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-06T11:37:01Z
- **Completed:** 2026-03-06T11:42:11Z
- **Tasks:** 2
- **Files modified:** 16

## Accomplishments
- All 6 SQLAlchemy models with proper relationships, cascades, and constraints
- Alembic migration infrastructure generating and applying schema to SQLite with WAL mode
- 50 exercises seeded across 6 muscle groups with valid equipment types
- Full CLI: `python -m gymcoach_scripts migrate` and `python -m gymcoach_scripts seed`
- 8 passing tests covering migrations, foreign keys, WAL mode, seed count, muscle groups, equipment validation, and re-seeding

## Task Commits

Each task was committed atomically:

1. **Task 1: Scaffold scripts repo with models, engine, and Alembic migrations** - `ea6fe90` (feat)
2. **Task 2: Create exercise seed data and seed script with tests** - `229e2db` (feat)

## Files Created/Modified
- `../scripts/pyproject.toml` - Project config with dependencies and hatchling build
- `../scripts/gymcoach_scripts/db/models.py` - All 6 SQLAlchemy 2.0 models
- `../scripts/gymcoach_scripts/db/engine.py` - Engine with WAL mode and FK enforcement
- `../scripts/gymcoach_scripts/db/alembic/env.py` - Alembic config with render_as_batch
- `../scripts/gymcoach_scripts/db/alembic/alembic.ini` - Alembic settings
- `../scripts/gymcoach_scripts/db/alembic/versions/66dbb3d599cf_initial_schema.py` - Initial migration
- `../scripts/gymcoach_scripts/seed.py` - Seed command with --force flag
- `../scripts/gymcoach_scripts/seed_data/exercises.json` - 50 exercises across 6 groups
- `../scripts/gymcoach_scripts/cli.py` - Click group with migrate and seed commands
- `../scripts/gymcoach_scripts/__main__.py` - Module entry point
- `../scripts/gymcoach_scripts/migrate.py` - Migration command
- `../scripts/tests/test_migrations.py` - 3 migration tests
- `../scripts/tests/test_seed.py` - 5 seed tests
- `../scripts/tests/conftest.py` - Shared test fixtures

## Decisions Made
- Used hatchling as build backend so gymcoach_scripts is importable as an installed package (uv init --app --bare does not include a build system)
- Alembic env.py reads GYMCOACH_DB env var at call time rather than importing the cached DATABASE_URL from engine.py, enabling test isolation with temp databases

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added hatchling build backend for package installability**
- **Found during:** Task 1 (Alembic migration generation)
- **Issue:** uv init --app --bare creates a project without a build system, so gymcoach_scripts was not importable as a package. Alembic env.py could not import models.
- **Fix:** Added [build-system] with hatchling and [tool.hatch.build.targets.wheel] packages config to pyproject.toml
- **Files modified:** ../scripts/pyproject.toml
- **Verification:** uv sync succeeded, alembic migration generation worked
- **Committed in:** ea6fe90 (Task 1 commit)

**2. [Rule 1 - Bug] Fixed Alembic script template filename**
- **Found during:** Task 1 (Alembic migration generation)
- **Issue:** Template was named script.mako but Alembic expects script.py.mako
- **Fix:** Renamed to script.py.mako
- **Files modified:** ../scripts/gymcoach_scripts/db/alembic/script.py.mako
- **Verification:** Alembic revision --autogenerate succeeded
- **Committed in:** ea6fe90 (Task 1 commit)

**3. [Rule 1 - Bug] Fixed Alembic env.py DATABASE_URL caching issue**
- **Found during:** Task 1 (migration test failure)
- **Issue:** env.py imported DATABASE_URL from engine.py at module load time, so GYMCOACH_DB env var changes in tests were not reflected
- **Fix:** Changed _get_url() to read env var directly at call time instead of importing cached value
- **Files modified:** ../scripts/gymcoach_scripts/db/alembic/env.py
- **Verification:** All 3 migration tests pass with isolated temp databases
- **Committed in:** ea6fe90 (Task 1 commit)

---

**Total deviations:** 3 auto-fixed (2 bugs, 1 blocking)
**Impact on plan:** All auto-fixes necessary for correct operation. No scope creep.

## Issues Encountered
- uv was not installed on the system; installed via official installer script before proceeding

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Scripts repo fully scaffolded with working migrations and seed data
- Database schema ready for backend (Plan 01-03) to import and use
- Shared ../data/ directory created for SQLite database

## Self-Check: PASSED

All 11 files verified present. Both task commits (ea6fe90, 229e2db) verified in scripts repo.

---
*Phase: 01-foundation-and-schema*
*Completed: 2026-03-06*
