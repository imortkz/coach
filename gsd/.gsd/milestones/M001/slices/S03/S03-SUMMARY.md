---
id: S03
parent: M001
milestone: M001
provides:
  - Workout start from program template
  - Set logging with weight/reps (pre-filled from last session)
  - Rest timer between sets
  - Workout finish/discard flow with summary
requires:
  - slice: S02
    provides: Exercise and program CRUD, Pinia stores
affects:
  - S04
  - S05
key_files:
  - backend/app/workouts/routes.py
  - backend/app/workouts/models.py
  - frontend/src/views/ActiveWorkoutView.vue
  - frontend/src/stores/workouts.js
key_decisions:
  - Pre-fill from last completed workout per exercise, fallback to program template
  - Rest timer runs client-side with configurable duration
  - Discard removes workout entirely (no partial saves)
patterns_established:
  - Workout lifecycle: start → log sets → finish/discard
  - Pre-fill logic queries last workout for each exercise
observability_surfaces: []
drill_down_paths: []
duration: ~30 min (3 plans)
verification_result: passed
completed_at: 2026-03-06
---

# S03: Workout Logging

**Workout flow from program template: start, log sets with auto-pre-fill from last session, rest timer, finish with summary or discard.**

## What Happened

Retroactive summary — S03 was completed as part of the original v1.0 MVP build. Three plans were executed in ~30 minutes (the longest v1.0 slice). Workout logging endpoints were built with start/log-set/finish/discard lifecycle. The Vue frontend got an active workout view with pre-filled weight/reps from the last session and a rest timer. Finishing a workout shows a summary; discarding removes it entirely.

## Verification

- User starts a workout from a program
- Sets pre-fill with weight/reps from last session
- Rest timer counts down between sets
- Finish shows workout summary; discard removes workout

## Files Created/Modified

See `.planning/milestones/v1.0-phases/03-workout-logging/` for original task-level detail.
