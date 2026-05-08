---
phase: 05-analytics-and-data-tools
plan: 02
subsystem: cli
tags: [click, rich, json, csv, export, import, backup, sqlalchemy]

# Dependency graph
requires:
  - phase: 01-foundation
    provides: "SQLAlchemy models (Exercise, Program, Workout, WorkoutSet, Setting) and DB engine"
  - phase: 05-analytics-and-data-tools
    provides: "CLI group structure and seed_workout_data test fixture"
provides:
  - "JSON export with nested programs/workouts/settings"
  - "CSV export with flat workout log rows"
  - "JSON import with auto-backup and replace-all strategy"
  - "Click commands: gymcoach export (--format json|csv, -o) and gymcoach import FILE"
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns: [export-import-module-pattern, fk-safe-delete-insert-order, iso-datetime-serialization]

key-files:
  created:
    - "../scripts/gymcoach_scripts/export_import/__init__.py"
    - "../scripts/gymcoach_scripts/export_import/exporter.py"
    - "../scripts/gymcoach_scripts/export_import/importer.py"
    - "../scripts/gymcoach_scripts/export_import/commands.py"
    - "../scripts/tests/test_export_import.py"
  modified:
    - "../scripts/gymcoach_scripts/cli.py"

key-decisions:
  - "ISO datetime strings parsed back to datetime objects during import for SQLite compatibility"
  - "Exercise ID mapping during import to handle re-assigned auto-increment IDs"
  - "FK-safe delete order: WorkoutSet > Workout > ProgramSet > ProgramExercise > Program > Exercise > Setting"

patterns-established:
  - "Export/import module: exporter.py (pure functions) -> importer.py (backup + replace) -> commands.py (Click CLI)"
  - "Auto-backup before destructive import with timestamped filename"

requirements-completed: [SCRP-04]

# Metrics
duration: 3min
completed: 2026-03-07
---

# Phase 5 Plan 2: Data Export/Import CLI Commands Summary

**JSON and CSV data export with full-restore JSON import, auto-backup, and Click CLI commands for gymcoach export/import**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-07T16:03:59Z
- **Completed:** 2026-03-07T16:08:00Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- Pure export functions producing nested JSON and flat CSV workout log rows with 22 unit tests (TDD)
- Import with FK-safe delete order, auto-backup, round-trip data integrity verification
- Click commands wired to main CLI: `gymcoach export --format json|csv` and `gymcoach import FILE` with Rich output

## Task Commits

Each task was committed atomically:

1. **Task 1: Export/import logic and tests** - `2afe800` (test+feat, TDD)
2. **Task 2: Export/import Click commands and CLI wiring** - `07f9dbd` (feat)

_Note: Task 1 used TDD flow (tests written first, then implementation)_

## Files Created/Modified
- `gymcoach_scripts/export_import/__init__.py` - Package init
- `gymcoach_scripts/export_import/exporter.py` - Pure functions: export_all_json, export_workout_csv, write_csv_file
- `gymcoach_scripts/export_import/importer.py` - Pure functions: create_backup, import_data with FK-safe delete/insert
- `gymcoach_scripts/export_import/commands.py` - Click commands: export_cmd, import_cmd with Rich output
- `gymcoach_scripts/cli.py` - Added export and import command registration
- `tests/test_export_import.py` - 22 unit tests covering export structure, CSV rows, import replace, backup, round-trip

## Decisions Made
- ISO datetime strings must be parsed back to Python datetime objects during import (SQLite DateTime type rejects strings)
- Exercise IDs are re-mapped during import since auto-increment may assign new IDs after delete/re-insert
- Program created_at uses server_default on re-import rather than preserving original timestamp (acceptable for backup/restore)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed ISO datetime string rejection by SQLite**
- **Found during:** Task 1 (import implementation)
- **Issue:** SQLite DateTime column rejects ISO string values; import was passing raw strings from JSON export
- **Fix:** Added _parse_datetime helper to convert ISO strings back to datetime objects before inserting Workout rows
- **Files modified:** gymcoach_scripts/export_import/importer.py
- **Verification:** Round-trip test passes (export then import preserves all data)
- **Committed in:** 2afe800 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Essential for correctness. No scope creep.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- All Phase 5 plans complete (analytics CLI + data export/import)
- Full test suite passes (61 tests across analytics and export/import)

---
*Phase: 05-analytics-and-data-tools*
*Completed: 2026-03-07*
