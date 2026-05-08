---
phase: 02-exercise-and-program-management
plan: 01
subsystem: api, database
tags: [fastapi, sqlalchemy, alembic, crud, sqlite, tdd]

requires:
  - phase: 01-foundation
    provides: "Backend scaffold, SQLAlchemy models, test infrastructure"
provides:
  - "Exercise CRUD API (GET/POST/PUT/DELETE with filters)"
  - "ProgramSet model and migration (per-set targets)"
  - "Updated ProgramExercise without flat target columns"
  - "Frontend ProgramSet TypeScript interface"
affects: [02-02, 02-03, 02-04, 03-workout-logging]

tech-stack:
  added: []
  patterns:
    - "Sync FastAPI endpoints with db.query() and Depends(get_db)"
    - "Seeded vs custom exercise protection via is_custom flag"
    - "In-use deletion guard checking program_exercises FK"
    - "Alembic batch_alter_table with copy_from for SQLite constraint changes"

key-files:
  created:
    - "../backend/tests/test_exercises.py"
    - "../scripts/gymcoach_scripts/db/alembic/versions/dabbf370d0ee_add_program_sets_table_and_remove_flat_.py"
  modified:
    - "../backend/app/exercises/routes.py"
    - "../backend/app/exercises/schemas.py"
    - "../backend/app/exercises/models.py"
    - "../backend/app/programs/models.py"
    - "../backend/app/programs/schemas.py"
    - "../backend/tests/conftest.py"
    - "../scripts/gymcoach_scripts/db/models.py"
    - "../frontend/src/types/index.ts"

key-decisions:
  - "Used Alembic copy_from with model Table to drop UNIQUE constraint on exercises.name in SQLite"
  - "Exercise deletion checks program_exercises FK and returns 409 with program names"

patterns-established:
  - "CRUD route pattern: list with Query filters, get/create/update/delete with proper HTTP status codes"
  - "Seeded exercise protection: 403 on PUT/DELETE for is_custom=false"

requirements-completed: [EXER-01, EXER-02]

duration: 3min
completed: 2026-03-06
---

# Phase 2 Plan 1: Schema Migration and Exercise CRUD Summary

**ProgramSet model with Alembic migration, exercise CRUD API with filtering/protection, and 13 TDD test cases**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-06T12:52:10Z
- **Completed:** 2026-03-06T12:55:54Z
- **Tasks:** 2
- **Files modified:** 10

## Accomplishments
- Schema migration adding program_sets table, removing flat target columns from program_exercises, and dropping exercises.name UNIQUE constraint
- Full Exercise CRUD API with muscle_group, equipment, and search (ilike) filters
- Seeded exercise protection (403 on update/delete) and in-use deletion guard (409 with program names)
- 13 passing test cases via TDD (RED/GREEN)
- Frontend TypeScript types updated with ProgramSet interface

## Task Commits

Each task was committed atomically:

1. **Task 1: Schema migration and model updates** - scripts:`bfdf15a`, backend:`7b14332`, frontend:`10b162b` (feat)
2. **Task 2: Exercise CRUD API (TDD RED)** - backend:`d2efa9a` (test)
3. **Task 2: Exercise CRUD API (TDD GREEN)** - backend:`417c84a` (feat)

## Files Created/Modified
- `../scripts/gymcoach_scripts/db/models.py` - Added ProgramSet model, removed flat targets from ProgramExercise, removed UNIQUE from Exercise.name
- `../scripts/gymcoach_scripts/db/alembic/versions/dabbf370d0ee_*.py` - Alembic migration for schema changes
- `../backend/app/exercises/routes.py` - Full CRUD endpoints with filters and protection
- `../backend/app/exercises/schemas.py` - Added ExerciseCreate, ExerciseUpdate schemas
- `../backend/app/exercises/models.py` - Removed UNIQUE from Exercise.name
- `../backend/app/programs/models.py` - Added ProgramSet, updated ProgramExercise
- `../backend/app/programs/schemas.py` - Added ProgramSetRead, updated ProgramExerciseRead/ProgramRead
- `../backend/tests/conftest.py` - Added ProgramSet import
- `../backend/tests/test_exercises.py` - 13 test cases for exercise CRUD
- `../frontend/src/types/index.ts` - Added ProgramSet interface, updated ProgramExercise

## Decisions Made
- Used Alembic `copy_from=Exercise.__table__` with `recreate='always'` to drop UNIQUE constraint on exercises.name in SQLite (standard `drop_constraint` doesn't work without naming convention)
- Exercise deletion returns 409 with specific program names in error detail for user-friendly feedback

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed Alembic migration for SQLite UNIQUE constraint drop**
- **Found during:** Task 1 (Schema migration)
- **Issue:** Alembic autogenerate did not detect the exercises.name UNIQUE constraint removal, and `drop_constraint` failed because SQLite unnamed constraints cannot be found by name
- **Fix:** Used `batch_alter_table` with `copy_from=Exercise.__table__` and `recreate='always'` to rebuild the table from model metadata
- **Files modified:** ../scripts/gymcoach_scripts/db/alembic/versions/dabbf370d0ee_*.py
- **Verification:** Migration runs clean, exercises DDL confirmed no UNIQUE constraint
- **Committed in:** bfdf15a (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Fix necessary for SQLite compatibility. No scope creep.

## Issues Encountered
None beyond the Alembic UNIQUE constraint issue documented above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Exercise CRUD API ready for frontend consumption (Plan 02-03/02-04)
- ProgramSet model ready for Program CRUD API (Plan 02-02)
- All 15 backend tests passing (13 exercise + 2 health)

---
*Phase: 02-exercise-and-program-management*
*Completed: 2026-03-06*
