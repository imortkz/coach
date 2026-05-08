---
phase: 06-integration-fixes-and-polish
plan: 01
subsystem: scripts, ui
tags: [import, export, datetime, vue, program-builder]

# Dependency graph
requires:
  - phase: 05-analytics-and-data-tools
    provides: export/import CLI and analytics queries
provides:
  - program_id FK remapping during import for data integrity
  - rest_timer_disabled toggle in program builder UI
  - deprecation-safe datetime usage across scripts
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "ID remapping pattern: build id_map dict during parent insert, use .get() for child FK resolution"

key-files:
  created: []
  modified:
    - "../scripts/gymcoach_scripts/export_import/importer.py"
    - "../scripts/tests/test_export_import.py"
    - "../frontend/src/stores/programs.ts"
    - "../frontend/src/views/ProgramEditView.vue"
    - "../scripts/gymcoach_scripts/analytics/queries.py"
    - "../scripts/tests/test_analytics.py"
    - "../scripts/tests/conftest.py"

key-decisions:
  - "Used datetime.now(timezone.utc).replace(tzinfo=None) to stay compatible with naive SQLite datetime storage"
  - "Forced ID offset in round-trip test to expose FK remapping bug that autoincrement masks"

patterns-established:
  - "ID remapping: always build {old_id: new_id} maps for all entity types during import"

requirements-completed: [SCRP-04, LOG-04]

# Metrics
duration: 3min
completed: 2026-03-07
---

# Phase 6 Plan 1: Integration Fixes Summary

**Import program_id FK remapping, rest_timer_disabled UI toggle, and datetime.utcnow() deprecation cleanup**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-07T16:32:22Z
- **Completed:** 2026-03-07T16:35:16Z
- **Tasks:** 3
- **Files modified:** 7

## Accomplishments
- Fixed import program_id FK remapping so round-trip export/import preserves workout-to-program links
- Added rest_timer_disabled checkbox to program builder with edit-mode loading
- Eliminated all datetime.utcnow() deprecation warnings (4 occurrences across 3 files)

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix import program_id FK remapping with test** - `79740ec` (fix) [scripts repo]
2. **Task 2: Add rest_timer_disabled toggle to program builder UI** - `95deff0` (feat) [frontend repo]
3. **Task 3: Fix datetime.utcnow() deprecation warnings** - `7d7965b` (fix) [scripts repo]

## Files Created/Modified
- `../scripts/gymcoach_scripts/export_import/importer.py` - Added program_id_map for FK remapping during import
- `../scripts/tests/test_export_import.py` - Added test_round_trip_preserves_program_links with forced ID offset
- `../frontend/src/stores/programs.ts` - Added rest_timer_disabled to ProgramCreatePayload interface
- `../frontend/src/views/ProgramEditView.vue` - Added restTimerDisabled ref, checkbox toggle, edit-mode loading, payload inclusion
- `../scripts/gymcoach_scripts/analytics/queries.py` - Replaced datetime.utcnow() with timezone-aware alternative
- `../scripts/tests/test_analytics.py` - Replaced 2 datetime.utcnow() calls
- `../scripts/tests/conftest.py` - Replaced datetime.utcnow() in seed fixture

## Decisions Made
- Used `datetime.now(timezone.utc).replace(tzinfo=None)` instead of `datetime.now(timezone.utc)` to maintain compatibility with naive datetime storage in SQLite
- Used `(program as any).rest_timer_disabled` cast in ProgramEditView since the Program type from API may not include the field in the TypeScript type definition yet

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Initial TDD RED test for program_id remapping passed unexpectedly because in-memory SQLite autoincrement IDs happened to match. Fixed by adding ID offset (1000) to exported data to force mismatch, properly exposing the bug.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All three audit gaps (INT-01, INT-02, deprecation warnings) are closed
- Full test suite (62 tests) passes with -W error::DeprecationWarning flag
- TypeScript compiles cleanly

## Self-Check: PASSED

All 7 modified files verified on disk. All 3 task commits verified in git log (scripts: 79740ec, 7d7965b; frontend: 95deff0).

---
*Phase: 06-integration-fixes-and-polish*
*Completed: 2026-03-07*
