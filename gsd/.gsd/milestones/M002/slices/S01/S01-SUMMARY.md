---
id: S01
parent: M002
milestone: M002
provides:
  - Edit button in swipe action panel rendered only for logged sets
  - Swipe enabled for all set row types (logged, extra, template)
  - isTemplate computed distinguishes unlogged non-extra sets
  - removeTemplate emit chain: SetRow → ExerciseCard → ActiveWorkout
  - skippedTemplateSets ref in ActiveWorkout tracks dismissed template set rows session-locally
  - Undo toast restores skipped template sets; no backend call on skip
requires: []
affects: []
key_files:
  - ../frontend/src/components/workout/SetRow.vue
  - ../frontend/src/components/workout/ExerciseCard.vue
  - ../frontend/src/components/workout/ActiveWorkout.vue
key_decisions:
  - D021: M002 planned as single slice with 3 tasks — all fixes touch the same component chain
  - D022: skippedTemplateSets keyed by "exerciseId:setNumber" strings in a Set
patterns_established:
  - Session-scoped skip state uses ref<Set<string>> with composite key "exerciseId:setNumber"
  - Set replacement (new Set(existing)) forces Vue 3 reactivity on Set mutations inside ref
observability_surfaces:
  - none
drill_down_paths:
  - .gsd/milestones/M002/slices/S01/tasks/T01-SUMMARY.md
  - .gsd/milestones/M002/slices/S01/tasks/T02-SUMMARY.md
  - .gsd/milestones/M002/slices/S01/tasks/T03-SUMMARY.md
duration: ~45 min
verification_result: passed
completed_at: 2026-03-14
---

# S01: Fix swipe actions and add template set skipping

**Three targeted SetRow.vue / ExerciseCard.vue / ActiveWorkout.vue changes make the swipe action panel contextually correct for all set types and add session-only template set skipping with undo toast.**

## What Happened

**T01** added `v-if="isLogged"` to the Edit button in SetRow.vue's swipe action panel. The panel container already excluded unlogged sets from rendering, but the Edit button inside was unconditionally rendered — meaning extra sets showed a non-functional Edit button. One attribute fixed this.

**T02** expanded swipe access to unlogged template sets. The `useSwipeLeft` callback guard (`if (isLogged || isExtra)`) was removed entirely so all rows can be swiped. A new `isTemplate` computed (`!isLogged && !isExtra`) was added. The action panel `v-if` was simplified to `showActions`. In `handleDelete`, a template branch fires first: emit `removeTemplate` with `{ exerciseId, setNumber }`. ExerciseCard was updated to declare the `removeTemplate` emit and bubble it upward via a `handleRemoveTemplate` pass-through.

**T03** wired the session state and undo integration in ActiveWorkout. `const skippedTemplateSets = ref(new Set<string>())` was added alongside the existing `removedExerciseIds` pattern. `handleRemoveTemplate` computes the composite key, replaces the Set (to trigger Vue reactivity), and calls `showUndoToastFn('Set skipped', ...)` with a restore callback and a no-op delete function (no backend call needed). The prop and event are bound on every ExerciseCard in the v-for loop. ExerciseCard accepts the `skippedTemplateSets` prop and filters template rows from its `setRows` computed when their key is present in the set.

## Verification

- `cd ../frontend && npm run build` — ✅ built in 1.24s, no errors
- Edit button has `v-if="isLogged"` guard — confirmed via grep
- `isTemplate` computed present in SetRow.vue — confirmed
- `removeTemplate` emit defined in SetRow (line 29), handled and re-emitted in ExerciseCard (lines 25, 148, 262) — confirmed
- `skippedTemplateSets` ref, `handleRemoveTemplate`, and `showUndoToastFn('Set skipped', ...)` all present in ActiveWorkout — confirmed
- ExerciseCard filters via `skippedTemplateSets.has(...)` in setRows computed — confirmed

## Requirements Advanced

- none (these are bug fixes and UX gaps with no corresponding Active requirements)

## Requirements Validated

- none

## New Requirements Surfaced

- none

## Requirements Invalidated or Re-scoped

- none

## Deviations

- **Set replacement for reactivity (T03):** Plan said "add to the set," implementation used `new Set(skippedTemplateSets.value)` replacement to force Vue 3 reactivity. Vue 3 `ref` does not deeply observe `Set` mutations — replacement is necessary for correct reactive behavior.

## Known Limitations

- `skippedTemplateSets` is component-local state: cleared when ActiveWorkout unmounts. This is intentional per spec (session-only). Refreshing the page during a workout restores all template sets.

## Follow-ups

- none

## Files Created/Modified

- `../frontend/src/components/workout/SetRow.vue` — `v-if="isLogged"` on Edit button; swipe guard removed; `isTemplate` computed; `removeTemplate` emit; `handleDelete` branched; action panel `v-if` simplified
- `../frontend/src/components/workout/ExerciseCard.vue` — `skippedTemplateSets` prop; `removeTemplate` emit; `handleRemoveTemplate` pass-through; `@remove-template` wired on SetRow; filter in setRows computed
- `../frontend/src/components/workout/ActiveWorkout.vue` — `skippedTemplateSets` ref; `handleRemoveTemplate` handler with undo toast; prop and event binding on ExerciseCard

## Forward Intelligence

### What the next slice should know
- The undo toast infrastructure (`showUndoToastFn`, `pendingDeletes`) in ActiveWorkout is now used for three distinct operations: deleting a set, removing an exercise, and skipping a template set. The pattern is stable and extensible.
- `skippedTemplateSets` is session-scoped ref — it resets on component unmount. Any future work requiring persistence would need localStorage or a server call.

### What's fragile
- Set reactivity pattern (`new Set(existing)` replacement) — easy to accidentally revert to `.add()`/`.delete()` only, which silently breaks UI updates without throwing errors. The pattern must be applied consistently in both add and delete paths.

### Authoritative diagnostics
- Vue DevTools → ActiveWorkout component → `skippedTemplateSets` ref — inspect the Set contents during a workout to verify skip state.

### What assumptions changed
- Plan assumed swipe guard needed to be "relaxed" — actual implementation removed it entirely. Simpler than expected; all rows benefit from unconditional swipe.
