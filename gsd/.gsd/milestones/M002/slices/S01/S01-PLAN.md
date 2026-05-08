# S01: Fix swipe actions and add template set skipping

**Goal:** Make the swipe action panel contextually correct for all set row types, and allow users to skip unlogged template sets during a workout with undo support.
**Demo:** In an active workout, swipe an unlogged extra set → only Delete shows (no Edit). Swipe a logged set → Edit + Delete. Swipe an unlogged template set → Delete; tap it → row disappears, undo toast appears; tap Undo → row returns. Start a new workout → all template sets present.

## Must-Haves

- Edit button hidden on unlogged sets (extra or template)
- Swipe enabled on unlogged template set rows
- Delete on template set emits `removeTemplate` (not `delete` or `removeExtra`)
- `skippedTemplateSets` ref in `ActiveWorkout.vue` tracks skipped sets as `"exerciseId:setNumber"` strings
- Undo toast restores skipped set by removing from `skippedTemplateSets`
- No backend API call when skipping a template set
- `skippedTemplateSets` is component-local state — not persisted, cleared on unmount

## Verification

- `cd ../frontend && npm run build` — no build errors
- Browser: swipe unlogged extra set → no Edit button visible
- Browser: swipe logged set → Edit + Delete both visible
- Browser: swipe unlogged template set → Delete visible; tap → row hidden, undo toast shown
- Browser: tap Undo → row restored
- Browser: complete/discard workout, start new one → all template sets present

## Tasks

- [x] **T01: Guard Edit button on isLogged and fix action panel conditions** `est:15m`
  - Why: Edit button silently no-ops on unlogged sets because `enterEditMode()` guards with `if (!isLogged)`. The button should not be visible at all on unlogged sets.
  - Files: `../frontend/src/components/workout/SetRow.vue`
  - Do: Add `v-if="isLogged"` (or equivalent) to the Edit button in the swipe action panel. Verify the action panel `v-if` still shows for logged and extra sets. The existing `v-if="showActions && (isLogged || isExtra)"` on the panel itself is correct for now — T02 will expand it to include template sets.
  - Verify: `cd ../frontend && npm run build` passes. Read the template to confirm Edit button has the guard.
  - Done when: Edit button element has a conditional that prevents rendering when set is not logged.

- [x] **T02: Enable swipe on unlogged template sets and route delete correctly** `est:30m`
  - Why: Unlogged template sets currently can't be swiped — the guard in the `useSwipeLeft` callback and the action panel `v-if` both exclude them. Need to enable swipe and add a third delete branch for template sets.
  - Files: `../frontend/src/components/workout/SetRow.vue`, `../frontend/src/components/workout/ExerciseCard.vue`
  - Do:
    1. In `SetRow.vue`: Relax the swipe guard to also allow unlogged template sets (not `isLogged` and not `isExtra` — i.e., the remaining case). Update the action panel `v-if` to match. Add an `isTemplate` computed (not logged, not extra = template). In `handleDelete`, add a branch: if `isTemplate`, emit `removeTemplate` with `{ exerciseId, setNumber }`. Define the `removeTemplate` emit.
    2. In `ExerciseCard.vue`: Listen for `@removeTemplate` from `SetRow` and re-emit it upward to `ActiveWorkout`.
  - Verify: `cd ../frontend && npm run build` passes. Read both files to confirm the new emit chain exists.
  - Done when: Swipe guard allows template sets, action panel shows for them, `removeTemplate` emit flows from SetRow → ExerciseCard.

- [x] **T03: Wire skippedTemplateSets state with undo in ActiveWorkout** `est:30m`
  - Why: The skip action needs session-scoped state and undo toast integration. This task wires the `removeTemplate` event to reactive state and the existing undo infrastructure.
  - Files: `../frontend/src/components/workout/ActiveWorkout.vue`, `../frontend/src/components/workout/ExerciseCard.vue`
  - Do:
    1. In `ActiveWorkout.vue`: Add `const skippedTemplateSets = ref(new Set<string>())`. Handle `removeTemplate` event from `ExerciseCard`: add `"exerciseId:setNumber"` to the set, call `showUndoToastFn` with a restore callback that removes the key from the set. No backend API call — unlike `handleDeleteSet`, there's nothing to delete server-side. Pass `skippedTemplateSets` as a prop to each `ExerciseCard`.
    2. In `ExerciseCard.vue`: Accept `skippedTemplateSets` prop. In the `setRows` computed, filter out template rows whose `"exerciseId:setNumber"` key is in `skippedTemplateSets`.
  - Verify: `cd ../frontend && npm run build` passes. Read both files to confirm prop flow and undo handler.
  - Done when: Skipping a template set hides it from the exercise card, undo restores it, and starting a new workout shows all sets.

## Files Likely Touched

- `../frontend/src/components/workout/SetRow.vue`
- `../frontend/src/components/workout/ExerciseCard.vue`
- `../frontend/src/components/workout/ActiveWorkout.vue`
