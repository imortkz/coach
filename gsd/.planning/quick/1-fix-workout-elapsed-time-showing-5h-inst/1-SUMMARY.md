---
phase: quick
plan: 1
subsystem: ui
tags: [vue, datetime, utc, timezone]

requires:
  - phase: 06-integration-fixes
    provides: Naive UTC datetime storage pattern
provides:
  - Z-suffix normalization for all datetime parsing in frontend
affects: []

tech-stack:
  added: []
  patterns:
    - "UTC datetime normalization: always append Z suffix before new Date() parsing"

key-files:
  created: []
  modified:
    - ../frontend/src/components/workout/ActiveWorkout.vue
    - ../frontend/src/components/history/WorkoutCard.vue

key-decisions:
  - "Applied same Z-suffix pattern already used in WorkoutSummary.vue for consistency"

patterns-established:
  - "UTC datetime parsing: raw.endsWith('Z') ? raw : raw + 'Z' before new Date()"

requirements-completed: []

duration: 2min
completed: 2026-03-07
---

# Quick Task 1: Fix Workout Elapsed Time Summary

**Z-suffix normalization on UTC datetime parsing in ActiveWorkout and WorkoutCard to fix 5h timezone offset**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-07T16:43:07Z
- **Completed:** 2026-03-07T16:45:00Z
- **Tasks:** 1
- **Files modified:** 2

## Accomplishments
- Fixed elapsed time in active workout header showing ~5h offset instead of actual minutes
- Fixed duration display in workout history cards showing incorrect durations
- Applied consistent Z-suffix normalization pattern matching existing WorkoutSummary.vue fix

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix UTC datetime parsing in ActiveWorkout.vue and WorkoutCard.vue** - `f0cf90e` (fix) -- frontend repo

## Files Modified
- `../frontend/src/components/workout/ActiveWorkout.vue` - Z-suffix on started_at in durationText computed
- `../frontend/src/components/history/WorkoutCard.vue` - Z-suffix on started_at and completed_at in durationDisplay computed

## Decisions Made
- Applied same Z-suffix pattern already used in WorkoutSummary.vue for consistency across all datetime parsing

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

---
*Quick task 1: fix-workout-elapsed-time*
*Completed: 2026-03-07*
