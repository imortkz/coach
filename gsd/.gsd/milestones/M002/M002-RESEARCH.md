# M002 — Research

**Date:** 2026-03-14

## Summary

All three bugs live in a tight three-component chain: `ActiveWorkout.vue` → `ExerciseCard.vue` → `SetRow.vue`. The code is clean and well-structured; there is no need for new composables, backend changes, or stores. The existing undo toast infrastructure (`showUndoToastFn` + `pendingDeletes`) in `ActiveWorkout` is exactly the right pattern for the template-set skip feature — it just needs a new caller and a parallel reactive ref for skipped sets (mirroring `removedExerciseIds`).

The Edit button bug is the simplest fix: the swipe panel already conditionally renders `v-if="showActions && (isLogged || isExtra)"`, but the Edit button inside that panel has no extra guard — it calls `enterEditMode()` which then silently no-ops (`if (!isLogged.value || !props.loggedSet) return`). Fix is to hide the Edit button when `!isLogged`, making the action panel context-aware. The Delete button stays in all cases.

The template-set skip feature requires: (1) a new `skippedTemplateSets` ref in `ActiveWorkout` (same shape as `removedExerciseIds` but keyed by `{exerciseId, setNumber}`), (2) passing it down as a prop to `ExerciseCard` which filters `setRows`, (3) a new `removeTemplate` emit from `SetRow`, and (4) enabling swipe on unlogged template sets. Session-only — no backend call needed.

## Recommendation

Implement in three clean commits ordered by risk:
1. **Fix Edit button** — purely cosmetic, zero data risk. Add `v-if="isLogged"` to the Edit button in `SetRow`'s swipe panel.
2. **Enable swipe on unlogged template sets with Delete action** — change the `useSwipeLeft` guard from `if (isLogged.value || props.isExtra)` to also include unlogged template sets; add a `removeTemplate` emit; handle it up the chain.
3. **Wire skipped-set state in `ActiveWorkout`** — new `skippedTemplateSets` ref, prop flow down, undo toast call.

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| Undo toast with timeout and flush-on-navigate | `showUndoToastFn` + `pendingDeletes` in `ActiveWorkout` | Already handles dedup, timeout, pending queue — identical pattern needed for skip |
| Swipe gesture detection | `useSwipeLeft` composable | Threshold + axis discrimination already correct; just needs the guard condition relaxed |
| Session-scoped exercise removal | `removedExerciseIds` ref in `ActiveWorkout` | Same pattern applies to skipped template sets — Set keyed by `${exerciseId}:${setNumber}` |

## Existing Code and Patterns

- `../frontend/src/components/workout/SetRow.vue` — owns swipe guard (`if (isLogged.value || props.isExtra)`), `showActions` ref, swipe action panel (`v-if="showActions && (isLogged || isExtra)"`), Edit/Delete buttons. Edit button calls `enterEditMode()` which guards on `isLogged` — the outer panel condition allows unlogged extras in, but Edit silently no-ops. Fix: add `v-if="isLogged"` on the Edit button. For template-set skip: add `isTemplate` computed, relax swipe guard, emit `removeTemplate`.
- `../frontend/src/components/workout/ExerciseCard.vue` — builds `setRows` computed; knows `isExtra` per row; passes `extraSetNumbers` prop down. For skip: accept `skippedTemplateSets` prop, filter template rows out of `setRows`, emit `removeTemplate` upward.
- `../frontend/src/components/workout/ActiveWorkout.vue` — owns `removedExerciseIds`, `extraSets`, `showUndoToastFn`, `pendingDeletes`. For skip: add `skippedTemplateSets` ref (Set of `"exerciseId:setNumber"` strings), handler that calls `showUndoToastFn` with add/remove logic (no backend call on the delete side, unlike `handleDeleteSet`).
- `../frontend/src/composables/useSwipeLeft.ts` — simple touchstart/touchend handler; threshold 60px horizontal with axis discrimination. No changes needed.

## Constraints

- Frontend only — no backend changes, no new endpoints.
- Skipped template sets must not persist beyond the current workout session. `skippedTemplateSets` lives in the component ref, cleared when `ActiveWorkout` is unmounted (workout complete or discarded).
- `showUndoToastFn` flushes the prior pending delete when a second one arrives — acceptable per existing precedent (documented in context).
- `ExerciseCard` receives `templateSets` as a prop from `ActiveWorkout` (actually from program data). The filter for skipped sets must happen inside `ExerciseCard.setRows` computed, not in `ActiveWorkout`, to avoid touching program data.

## Common Pitfalls

- **Swipe guard is in two places** — `useSwipeLeft` callback has the guard (`if (isLogged.value || props.isExtra) { showActions.value = true }`), and the action panel has `v-if="showActions && (isLogged || isExtra)"`. Both need updating when adding template-set swipe support. Miss one and the panel either never shows or shows at the wrong time.
- **`isExtra` check on Delete in `handleDelete`** — the existing delete handler branches on `isExtra && !loggedSet` → `emit('removeExtra')`. Need a third branch: unlogged template set → `emit('removeTemplate')`. Falling through to `emit('delete', props.loggedSet.id)` when `loggedSet` is null would be a silent no-op, but it's a logic hazard worth closing explicitly.
- **Set number gaps after skip** — context doc confirms cosmetic gap is acceptable. Don't renumber; it would break `loggedSets.find()` matching logic which matches on `set_number`.
- **`skippedTemplateSets` not passed to `ExerciseCard` for exercises added mid-workout** — exercises from `orderedExercises` (filtered program exercises) all need the prop; the `v-for` binding handles all of them uniformly, so no special-casing needed.
- **Undo restores the row but the user may have already logged another set** — restoring a skipped template set that was later replaced by an extra logged set is benign (it shows up as an unlogged template row). No conflict to handle.

## Open Risks

- If a template set is skipped and then the user immediately swipes a logged set and sees the undo toast replaced — the skipped set cannot be undeleted. Acceptable per existing precedent; no new risk introduced.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| Vue 3 / Tailwind | (none needed) | n/a — straightforward component edits |

## Sources

- Full source read: `SetRow.vue`, `ExerciseCard.vue`, `ActiveWorkout.vue`, `useSwipeLeft.ts`
