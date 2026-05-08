---
id: M002
provides:
  - Edit button in swipe action panel rendered only for logged sets (v-if="isLogged" guard)
  - Swipe-to-delete enabled for all set row types including unlogged template sets
  - Session-only template set skipping with undo toast (no backend call, no program modification)
  - skippedTemplateSets ref in ActiveWorkout tracks dismissed rows via composite "exerciseId:setNumber" keys
  - removeTemplate emit chain wired through SetRow → ExerciseCard → ActiveWorkout
key_decisions:
  - D021: M002 planned as single slice with 3 tasks — all fixes touch the same component chain
  - D022: skippedTemplateSets keyed by "exerciseId:setNumber" strings in a Set
patterns_established:
  - Session-scoped skip state uses ref<Set<string>> with composite key "exerciseId:setNumber"
  - Set replacement (new Set(existing)) forces Vue 3 reactivity on Set mutations inside ref
  - Undo toast infrastructure (showUndoToastFn + pendingDeletes) now covers three operations: delete set, remove exercise, skip template set
observability_surfaces:
  - none
requirement_outcomes: []
duration: ~45 min
verification_result: passed
completed_at: 2026-03-14
---

# M002: Workout Set UX Fixes

**Three targeted frontend changes to SetRow.vue, ExerciseCard.vue, and ActiveWorkout.vue make the swipe action panel contextually correct for all set types and add session-only template set skipping with undo toast.**

## What Happened

M002 was executed as a single slice (S01) with three sequential tasks targeting the SetRow → ExerciseCard → ActiveWorkout component chain.

**T01** fixed the Edit button visibility bug. The swipe action panel already excluded unlogged sets from rendering the panel container, but the Edit button inside was rendered unconditionally — meaning extra sets (unlogged) showed a non-functional Edit button. Adding `v-if="isLogged"` to the Edit button element fixed this with a one-line change.

**T02** expanded swipe access to unlogged template sets. The `useSwipeLeft` callback guard (`if (isLogged || isExtra)`) was removed entirely so all rows can be swiped. A new `isTemplate` computed (`!isLogged && !isExtra`) was added to distinguish template set rows. The action panel `v-if` was simplified to `showActions`. In `handleDelete`, a template branch fires first: it emits `removeTemplate` with `{ exerciseId, setNumber }` instead of calling the delete API. ExerciseCard was updated to declare the `removeTemplate` emit and bubble it upward via a `handleRemoveTemplate` pass-through handler.

**T03** wired session state and undo integration in ActiveWorkout. `const skippedTemplateSets = ref(new Set<string>())` was added alongside the existing `removedExerciseIds` pattern. `handleRemoveTemplate` computes the composite key (`"exerciseId:setNumber"`), replaces the Set using `new Set(existing)` to trigger Vue 3 reactivity, then calls `showUndoToastFn('Set skipped', ...)` with a restore callback (which deletes the key and replaces the Set again) and a no-op delete function (no backend call needed — the set was never logged). The prop and event binding were added to every ExerciseCard in the v-for loop. ExerciseCard accepts the `skippedTemplateSets` prop and filters template rows from its `setRows` computed when their key is present in the set.

## Cross-Slice Verification

**Success criterion: Edit only appears on logged sets**
- `v-if="isLogged"` present on Edit button in SetRow.vue at line 309 — confirmed via grep
- Build passes clean (`✓ built in 1.19s`, no errors or warnings)

**Success criterion: Swipe works on unlogged template set rows**
- `useSwipeLeft` guard removed; `isTemplate` computed present in SetRow.vue at line 74 — confirmed via grep
- `removeTemplate` emit declared in SetRow.vue at line 29 — confirmed

**Success criterion: Tapping Delete on an unlogged template set hides the row and shows undo toast**
- `handleDelete` branches on `isTemplate.value` at line 138, emitting `removeTemplate` instead of calling delete API — confirmed
- `handleRemoveTemplate` in ActiveWorkout adds key to `skippedTemplateSets` and calls `showUndoToastFn('Set skipped', ...)` at lines 184–196 — confirmed
- ExerciseCard filters skipped rows in `setRows` computed via `.has(key)` check at line 49 — confirmed

**Success criterion: Undo restores the skipped template set row**
- Restore callback in `handleRemoveTemplate` deletes the key from the Set and replaces with `new Set(existing)` at lines 194–195 — confirmed

**Success criterion: Starting a new workout shows all template sets**
- `skippedTemplateSets` is component-local `ref` — cleared automatically when ActiveWorkout unmounts. No persistence, no backend state — confirmed by design (D022)

**Success criterion: No program data modified in MongoDB**
- No API call is made in the `removeTemplate` path — `handleRemoveTemplate` in ActiveWorkout contains no `apiFetch` or store action call — confirmed via grep (no fetch in the function body)

**Build verification:**
- `cd ../frontend && npm run build` → `✓ built in 1.19s, no errors` — confirmed

## Requirement Changes

- No requirements changed status during this milestone — all three fixes were bug fixes and UX gaps with no corresponding Active requirements.

## Forward Intelligence

### What the next milestone should know
- The undo toast infrastructure (`showUndoToastFn`, `pendingDeletes`) in ActiveWorkout now handles three distinct operations: deleting a logged set (API call), removing an exercise (API call), and skipping a template set (no API call). The pattern is stable and extensible for future session-scoped operations.
- `skippedTemplateSets` is component-local state scoped to the ActiveWorkout instance. Refreshing the browser during a workout resets it — all template sets reappear. This is intentional per spec.

### What's fragile
- **Set reactivity pattern** (`new Set(existing)` replacement) — easy to accidentally revert to `.add()`/`.delete()` only, which silently breaks UI updates without throwing errors. Both the add path (line 188) and delete/restore path (line 195) must use replacement. Code reviewers should watch for this.
- **Set number gaps** — if set 2 is skipped from a 3-set exercise, the remaining row shows "Set 3" with no renumbering. Confirmed acceptable cosmetically per M002 context, but may confuse users if set numbers become UI-meaningful in future milestones.

### Authoritative diagnostics
- Vue DevTools → ActiveWorkout component → `skippedTemplateSets` ref — inspect Set contents during a workout to verify skip state is tracked correctly.
- `grep -n "isLogged\|isTemplate\|showActions" ../frontend/src/components/workout/SetRow.vue` — verify swipe guard state at a glance.

### What assumptions changed
- Plan assumed swipe guard needed to be "relaxed" — actual implementation removed it entirely. Simpler than expected; all rows benefit from unconditional swipe access.
- Plan said "add to the set" for reactivity — implementation used `new Set(existing)` replacement because Vue 3 `ref` does not deeply observe `Set` mutations.

## Files Created/Modified

- `../frontend/src/components/workout/SetRow.vue` — `v-if="isLogged"` on Edit button; swipe guard removed; `isTemplate` computed added; `removeTemplate` emit declared; `handleDelete` branched for template vs non-template; action panel `v-if` simplified to `showActions`
- `../frontend/src/components/workout/ExerciseCard.vue` — `skippedTemplateSets` prop accepted; `removeTemplate` emit declared; `handleRemoveTemplate` pass-through handler added; `@remove-template` wired on SetRow; template row filter added in `setRows` computed
- `../frontend/src/components/workout/ActiveWorkout.vue` — `skippedTemplateSets` ref added; `handleRemoveTemplate` handler with undo toast and no-op delete; `:skipped-template-sets` prop and `@remove-template` event bound on ExerciseCard v-for
