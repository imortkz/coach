# M002: Workout Set UX Fixes — Context

**Gathered:** 2026-03-14
**Status:** Queued — pending auto-mode execution.

## Project Description

GymCoach is a personal gym training companion. Users log workouts against a program (set of exercises with target sets, reps, weight). During a workout session, each exercise shows its template sets from the program plus any extra sets the user adds.

## Why This Milestone

Three bugs/gaps were discovered in the active workout UI:

1. **Edit button does nothing** — The swipe-left action panel shows an "Edit" button on unlogged extra set rows, but `enterEditMode()` guards with `if (!isLogged)`, so it silently no-ops. Edit only makes sense for logged sets.
2. **Can't remove a template set during a workout** — Swipe actions are only enabled for `isLogged || isExtra`. Unlogged template sets have no removal path, but sometimes you want to skip a set that's prescribed in the program (e.g. you're running short on time, the set is too heavy today).
3. **Removal is session-only** — The program must not be modified. Skipped template sets are ephemeral state for the current workout only. Next workout starts from the program as-is.

## User-Visible Outcome

### When this milestone is complete, the user can:

- Swipe left on any set row (template or extra, logged or unlogged) and see contextually correct actions
- Remove an unlogged template set from the active workout view with undo toast; next workout that set is back
- No longer see a broken Edit button on extra sets that haven't been logged yet

### Entry point / environment

- Entry point: http://localhost:5173 — Workout tab → active workout → exercise card → swipe set row
- Environment: browser (mobile-first)
- Live dependencies involved: none (all frontend-only changes)

## Completion Class

- Contract complete means: all three behaviours verified in the browser against a running dev server
- Integration complete means: program not modified after skipping a template set; skipped set reappears on next workout start
- Operational complete means: none

## Final Integrated Acceptance

To call this milestone complete, we must prove:

- Swipe on an unlogged extra set shows only Delete (no Edit); swipe on a logged set still shows Edit + Delete
- Swipe on an unlogged template set shows Delete; tapping it hides the row and shows undo toast; tapping Undo restores it
- After starting a new workout from the same program, the previously skipped set is present again
- No changes committed to program data in MongoDB

## Risks and Unknowns

- Set number gaps — if set 2 is skipped from a 3-set exercise, the remaining row shows set 3. This is probably fine (cosmetic). Confirm during implementation whether renumbering is needed.
- Undo toast conflict — two undo toasts can't coexist (existing `showUndoToastFn` flushes the prior one). Skipping a template set and then deleting a logged set in quick succession will flush the first. Acceptable given existing precedent.

## Existing Codebase / Prior Art

- `../frontend/src/components/workout/SetRow.vue` — renders each set row; contains the swipe logic, `enterEditMode` guard bug, and the action panel template
- `../frontend/src/components/workout/ExerciseCard.vue` — builds `setRows` computed from template/logged/extra sets; manages `extraSets` ref; emits `deleteSet`, `removeExtra`, `removeExercise`
- `../frontend/src/components/workout/ActiveWorkout.vue` — owns session state (`removedExerciseIds`, `extraSets`, undo toast via `showUndoToastFn`); handles `deleteSet` with undo pattern to follow for skipped template sets
- `../frontend/src/stores/workouts.ts` — `deleteSet` calls `DELETE /api/workouts/:id/sets/:setId`; no backend call needed for skipping a template set (it was never logged)

> See `.gsd/DECISIONS.md` for all architectural and pattern decisions — it is an append-only register; read it during planning, append to it during execution.

## Relevant Requirements

No existing requirements directly map to this — these are bug fixes and a UX gap discovered during use.

## Scope

### In Scope

- Fix Edit button: hide it (or disable) on unlogged extra set rows — only show for logged sets
- Add swipe-reveal Delete action on unlogged template set rows
- Track skipped template sets in `ActiveWorkout` reactive state (session-only, same pattern as `removedExerciseIds`)
- Show undo toast on skip, consistent with logged set deletion behaviour

### Out of Scope / Non-Goals

- Modifying the program (sets, reps, weights) from within a workout
- Renumbering remaining sets after a skip (cosmetic gap is acceptable)
- Backend changes — no new endpoints, no schema changes
- Changing rest timer or suggestion logic for skipped sets

## Technical Constraints

- Frontend only — `../frontend/src/` is the only target
- Must not call any API for template set skipping (the set was never logged, nothing to delete on the backend)
- Session state must be lost when the workout is completed or discarded — no persistence of skipped sets

## Integration Points

- `ActiveWorkout.vue` → `ExerciseCard.vue` → `SetRow.vue` — the fix spans this component chain; skipped-set state originates in `ActiveWorkout`, flows down as a prop (like `extraSetNumbers`), and `SetRow` reacts to it
- `showUndoToastFn` in `ActiveWorkout` — reuse existing undo infrastructure

## Open Questions

- None — all design questions resolved during discussion.
