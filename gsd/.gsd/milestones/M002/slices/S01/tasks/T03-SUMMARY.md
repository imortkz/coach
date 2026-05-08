---
id: T03
parent: S01
milestone: M002
provides:
  - skippedTemplateSets ref in ActiveWorkout tracks dismissed template set rows session-locally
  - handleRemoveTemplate handler adds key and shows undo toast with restore callback (no backend call)
  - ExerciseCard filters skipped unlogged template rows from setRows computed
key_files:
  - ../frontend/src/components/workout/ActiveWorkout.vue
  - ../frontend/src/components/workout/ExerciseCard.vue
key_decisions:
  - Used Set replacement (new Set(existing)) instead of mutation to trigger Vue reactivity on skippedTemplateSets
  - showUndoToastFn deleteFn is a no-op for template skipping — template sets are session-only, no backend call needed
patterns_established:
  - Session-scoped skip state uses ref<Set<string>> with composite key "exerciseId:setNumber"
observability_surfaces:
  - none
duration: ~10 min
verification_result: passed
completed_at: 2026-03-14
blocker_discovered: false
---

# T03: Wire skippedTemplateSets state with undo in ActiveWorkout

**Added `skippedTemplateSets` ref to ActiveWorkout with undo toast support, and ExerciseCard now filters dismissed template rows from `setRows`.**

## What Happened

- Added `const skippedTemplateSets = ref(new Set<string>())` alongside `removedExerciseIds` in `ActiveWorkout.vue`.
- Added `handleRemoveTemplate({ exerciseId, setNumber })`: computes key as `"${exerciseId}:${setNumber}"`, replaces the Set to trigger reactivity, calls `showUndoToastFn('Set skipped', undoFn, noopDeleteFn)`. The restore callback deletes the key and again replaces the Set for reactivity. No backend call in the delete path.
- Passed `:skipped-template-sets="skippedTemplateSets"` and `@remove-template="handleRemoveTemplate"` on every ExerciseCard in the v-for loop.
- In `ExerciseCard.vue`: added `skippedTemplateSets?: Set<string>` prop (defaults to `new Set()`). In the `setRows` computed, template-defined set rows are skipped when the row has no logged set and `skippedTemplateSets.has("${exercise.id}:${ts.set_number}")`.

## Verification

- `cd ../frontend && npm run build` — ✅ built in 1.18s, no errors
- Grep: `skippedTemplateSets` exists in ActiveWorkout (ref, handler, template binding) — ✅
- Grep: `showUndoToastFn` called with `'Set skipped'` inside `handleRemoveTemplate` — ✅
- Grep: ExerciseCard filters via `skippedTemplateSets.has(...)` in setRows computed — ✅

## Diagnostics

none — state is session-scoped reactive ref; inspect via Vue DevTools if needed.

## Deviations

- Used `new Set(skippedTemplateSets.value)` to replace the ref value on each mutation, rather than direct `.add()`/`.delete()` alone. This is necessary because Vue 3's `ref` does not deeply observe `Set` mutations, so replacement forces reactivity. Not mentioned in plan but required for correct behavior.

## Known Issues

none

## Files Created/Modified

- `../frontend/src/components/workout/ActiveWorkout.vue` — added `skippedTemplateSets` ref, `handleRemoveTemplate` handler, prop and event binding on ExerciseCard
- `../frontend/src/components/workout/ExerciseCard.vue` — added `skippedTemplateSets` prop, filter logic in setRows computed
