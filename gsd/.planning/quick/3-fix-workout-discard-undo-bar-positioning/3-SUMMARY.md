---
phase: quick
plan: 3
subsystem: ui
tags: [vue, tailwind, mobile, undo-toast]

provides:
  - Repositioned undo toast just above mobile nav bar
  - Programs list visible during discard countdown
affects: [workout-view, mobile-ux]

key-files:
  modified:
    - ../frontend/src/components/workout/UndoToast.vue
    - ../frontend/src/components/workout/ActiveWorkout.vue

key-decisions:
  - "pointer-events-none + opacity-75 for non-interactive background content during discard"

requirements-completed: []

duration: 0.5min
completed: 2026-03-07
---

# Quick Task 3: Fix Workout Discard Undo Bar Positioning Summary

**Undo toast repositioned to bottom-20 (just above mobile nav) and ProgramPicker shown as faded background during discard countdown**

## Performance

- **Duration:** 30s
- **Started:** 2026-03-07T16:56:14Z
- **Completed:** 2026-03-07T16:56:44Z
- **Tasks:** 1
- **Files modified:** 2

## Accomplishments
- Undo toast now sits 16px above the mobile bottom nav bar (bottom-20 = 80px, nav = 64px)
- During discard countdown, ProgramPicker renders non-interactively (pointer-events-none, opacity-75) instead of a blank page
- Undo functionality unchanged -- existing logic already renders UndoToast outside the v-if block

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix undo toast positioning and show programs list during discard** - `288af3c` (fix) - frontend repo

## Files Modified
- `../frontend/src/components/workout/UndoToast.vue` - Changed bottom-32 to bottom-20, sm:bottom-16 to sm:bottom-4
- `../frontend/src/components/workout/ActiveWorkout.vue` - Added ProgramPicker import and v-else block for discard state

## Decisions Made
- Used pointer-events-none + opacity-75 on ProgramPicker to prevent accidental interaction during discard countdown while still showing useful content behind the undo bar

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

---
*Quick task: 3-fix-workout-discard-undo-bar-positioning*
*Completed: 2026-03-07*
