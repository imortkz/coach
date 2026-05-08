---
phase: quick
plan: 2
subsystem: ui
tags: [vue, reactivity, setInterval, timer]

requires:
  - phase: quick-1
    provides: "Fixed durationText to use started_at instead of created_at"
provides:
  - "Live-ticking elapsed timer in active workout header"
affects: []

tech-stack:
  added: []
  patterns: ["Reactive clock pattern: ref + setInterval + onUnmounted cleanup"]

key-files:
  created: []
  modified:
    - "../frontend/src/components/workout/ActiveWorkout.vue"

key-decisions:
  - "Merged setInterval setup into existing onMounted block for clarity"
  - "Separate onUnmounted hook for interval cleanup (not merged with flushPendingDeletes)"

patterns-established:
  - "Reactive clock: ref(Date.now()) + setInterval(60000) + onUnmounted cleanup for time-dependent computeds"

requirements-completed: [QUICK-2]

duration: 1min
completed: 2026-03-07
---

# Quick Task 2: Make Workout Elapsed Timer Reactive Summary

**Reactive elapsed timer using setInterval + ref so durationText recomputes every minute**

## Performance

- **Duration:** 1 min
- **Started:** 2026-03-07T16:48:52Z
- **Completed:** 2026-03-07T16:49:41Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- Added reactive `now` ref that updates every 60 seconds via setInterval
- durationText computed now depends on reactive ref, causing live re-evaluation
- Proper cleanup via onUnmounted prevents memory leaks

## Task Commits

Each task was committed atomically:

1. **Task 1: Add reactive timer tick to ActiveWorkout.vue** - `2c692a2` (feat)

## Files Created/Modified
- `../frontend/src/components/workout/ActiveWorkout.vue` - Added onUnmounted import, reactive `now` ref, setInterval in onMounted, clearInterval in onUnmounted, updated durationText to use `now.value`

## Decisions Made
- Merged setInterval setup into the existing onMounted block rather than adding a second onMounted call
- Used separate onUnmounted hook for interval cleanup to keep concerns separated from the existing flushPendingDeletes function

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

---
*Plan: quick-2*
*Completed: 2026-03-07*
