---
id: S02
parent: M001
milestone: M001
provides:
  - Exercise CRUD endpoints (list, create, update, delete)
  - Program CRUD with nested exercises and sets
  - Pinia stores for exercises and programs
  - Vue views for exercise and program management
requires:
  - slice: S01
    provides: Backend scaffold, DB schema, seed data
affects:
  - S03
  - S04
key_files:
  - backend/app/exercises/routes.py
  - backend/app/programs/routes.py
  - frontend/src/stores/exercises.js
  - frontend/src/stores/programs.js
  - frontend/src/views/ExercisesView.vue
  - frontend/src/views/ProgramsView.vue
key_decisions:
  - Programs contain ordered exercises with target sets (reps + weight)
  - Full CRUD exposed via REST; frontend uses Pinia stores
patterns_established:
  - Pinia store per domain entity with async API calls
  - Vue views consume Pinia stores for state management
observability_surfaces: []
drill_down_paths: []
duration: ~20 min (4 plans)
verification_result: passed
completed_at: 2026-03-06
---

# S02: Exercise and Program Management

**Full CRUD for exercises and programs with nested sets/reps/weight targets. Vue frontend with Pinia stores for both entities.**

## What Happened

Retroactive summary — S02 was completed as part of the original v1.0 MVP build. Four plans were executed in ~20 minutes. Exercise and program CRUD endpoints were built in FastAPI, Pinia stores created for frontend state, and Vue views wired up for managing exercises and building programs with ordered exercises and target sets.

## Verification

- User can create, edit, delete exercises
- User can build programs with ordered exercises and target sets

## Files Created/Modified

See `.planning/milestones/v1.0-phases/02-exercise-and-program-management/` for original task-level detail.
