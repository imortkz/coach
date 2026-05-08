---
estimated_steps: 5
estimated_files: 2
---

# T03: Wire skippedTemplateSets state with undo in ActiveWorkout

**Slice:** S01 — Fix swipe actions and add template set skipping
**Milestone:** M002

## Description

Connect the `removeTemplate` event to session-scoped reactive state in `ActiveWorkout.vue` with undo toast support. Pass the state down to `ExerciseCard` which filters skipped template rows from `setRows`. No backend call — template sets were never logged.

## Steps

1. Read `ActiveWorkout.vue` — locate `removedExerciseIds`, `showUndoToastFn`, and how `ExerciseCard` components are rendered
2. Add `const skippedTemplateSets = ref(new Set<string>())` alongside `removedExerciseIds`
3. Add `handleRemoveTemplate({ exerciseId, setNumber })` handler: compute key as `"${exerciseId}:${setNumber}"`, add to `skippedTemplateSets.value`, call `showUndoToastFn` with message like "Set skipped" and restore callback that deletes the key from the set. No `pendingDeletes` push needed (nothing to delete on backend).
4. Pass `:skipped-template-sets="skippedTemplateSets"` prop to each `ExerciseCard` in the template. Listen for `@removeTemplate="handleRemoveTemplate"`.
5. In `ExerciseCard.vue`: accept `skippedTemplateSets` prop (type `Set<string>`). In the `setRows` computed, filter out rows where the row is a template set (not logged, not extra) and `skippedTemplateSets.has("${exerciseId}:${setNumber}")`.

## Must-Haves

- [ ] `skippedTemplateSets` ref exists in ActiveWorkout
- [ ] `handleRemoveTemplate` adds key and calls `showUndoToastFn` with restore callback
- [ ] No backend API call made when skipping
- [ ] `skippedTemplateSets` passed as prop to ExerciseCard
- [ ] ExerciseCard filters skipped template rows from setRows computed
- [ ] Build passes

## Verification

- `cd ../frontend && npm run build` — no errors
- Grep: `skippedTemplateSets` exists in ActiveWorkout and is passed to ExerciseCard
- Grep: `showUndoToastFn` called in handleRemoveTemplate

## Inputs

- `../frontend/src/components/workout/ActiveWorkout.vue` — existing undo infrastructure (`showUndoToastFn`, `removedExerciseIds` pattern)
- `../frontend/src/components/workout/ExerciseCard.vue` — T02 output (already re-emits `removeTemplate`)

## Expected Output

- `../frontend/src/components/workout/ActiveWorkout.vue` — `skippedTemplateSets` ref, handler, prop binding
- `../frontend/src/components/workout/ExerciseCard.vue` — prop accepted, setRows filters skipped template sets
