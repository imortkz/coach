# M002: Workout Set UX Fixes

**Vision:** Fix swipe action panel so Edit only appears on logged sets, enable swipe-to-skip on unlogged template sets with undo, and keep skipped sets session-only (program unchanged).

## Success Criteria

- Swiping left on an unlogged extra set shows only Delete (no Edit button visible)
- Swiping left on a logged set shows both Edit and Delete
- Swiping left on an unlogged template set shows Delete; tapping it hides the row and shows an undo toast
- Tapping Undo on the toast restores the skipped template set row
- Starting a new workout from the same program shows all template sets (previously skipped sets are back)
- No program data is modified in MongoDB when a template set is skipped

## Key Risks / Unknowns

None — all three fixes are isolated frontend changes in well-understood components. The swipe guard, action panel, and undo toast patterns already exist and just need conditional adjustments.

## Verification Classes

- Contract verification: none (no backend changes, no tests to add)
- Integration verification: none (frontend-only, no new API calls)
- Operational verification: none
- UAT / human verification: browser verification against running dev server — swipe interactions on set rows across all three states (logged, unlogged extra, unlogged template)

## Milestone Definition of Done

This milestone is complete only when all are true:

- All three fixes are implemented in `SetRow.vue`, `ExerciseCard.vue`, and `ActiveWorkout.vue`
- Browser verification confirms: Edit hidden on unlogged sets, swipe works on template sets, skip + undo works, program data unchanged after skip
- Dev server at localhost:5173 demonstrates all behaviours in active workout view

## Requirement Coverage

- Covers: none (these are bug fixes and UX gaps with no corresponding Active requirements)
- Orphan risks: none — no Active requirements are relevant to this milestone

## Slices

- [x] **S01: Fix swipe actions and add template set skipping** `risk:low` `depends:[]`
  > After this: user can swipe any set row and see contextually correct actions; unlogged template sets can be skipped with undo; Edit only appears on logged sets; skipped sets reappear on next workout

## Boundary Map

### S01

Produces:
- `skippedTemplateSets` reactive Set in `ActiveWorkout.vue` (session-only, keyed by `"exerciseId:setNumber"` strings)
- `removeTemplate` emit from `SetRow.vue` → `ExerciseCard.vue` → `ActiveWorkout.vue`
- Contextual action panel: Edit button guarded by `isLogged`, Delete available on all swipeable rows

Consumes:
- Existing `showUndoToastFn` + `pendingDeletes` undo infrastructure in `ActiveWorkout.vue`
- Existing `useSwipeLeft` composable (no changes needed to the composable itself)
- Existing `removedExerciseIds` pattern as the model for `skippedTemplateSets`
