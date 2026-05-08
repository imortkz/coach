---
id: T02
parent: S01
milestone: M002
provides:
  - Swipe enabled for all set row types (logged, extra, template)
  - isTemplate computed distinguishes unlogged non-extra sets
  - handleDelete routes template sets to removeTemplate emit
  - ExerciseCard re-emits removeTemplate for parent consumption
key_files:
  - ../frontend/src/components/workout/SetRow.vue
  - ../frontend/src/components/workout/ExerciseCard.vue
key_decisions:
  - Removed the swipe guard condition entirely (was `isLogged || isExtra`) — all rows can now be swiped
  - isTemplate = !isLogged && !isExtra covers the new case cleanly
  - removeTemplate payload carries both exerciseId and setNumber (needed by parent to identify the row)
patterns_established:
  - none
observability_surfaces:
  - none
duration: short
verification_result: passed
completed_at: 2026-03-14
blocker_discovered: false
---

# T02: Enable swipe on unlogged template sets and route delete correctly

**Relaxed swipe guard to allow all set rows, added `isTemplate` computed, and routed template set deletes to a new `removeTemplate` emit bubbled through ExerciseCard.**

## What Happened

- Added `removeTemplate` emit to `SetRow.vue` with payload `{ exerciseId, setNumber }`
- Added `isTemplate` computed: `!isLogged.value && !props.isExtra`
- Removed the `if (isLogged.value || props.isExtra)` guard from the `useSwipeLeft` callback — swipe now triggers `showActions = true` unconditionally
- Removed the `isLogged || isExtra` condition from the action panel `v-if` — panel shows whenever `showActions` is true
- In `handleDelete`, added the template branch first: if `isTemplate`, emit `removeTemplate` and return
- In `ExerciseCard.vue`, added `removeTemplate` to the emits definition, added `handleRemoveTemplate` function, and wired `@remove-template="handleRemoveTemplate"` on `SetRow`

## Verification

- `cd ../frontend && npm run build` — clean build, no errors
- Grep confirms `removeTemplate` emit defined in SetRow (line 29) and handled/re-emitted in ExerciseCard (lines 23, 143)
- Swipe guard: `useSwipeLeft` callback now unconditionally sets `showActions.value = true`
- Action panel: `v-if="showActions"` (no extra condition)
- Delete routing: template branch fires before extra/logged branches

## Diagnostics

none

## Deviations

none — plan followed exactly

## Known Issues

none

## Files Created/Modified

- `../frontend/src/components/workout/SetRow.vue` — swipe guard removed, `isTemplate` computed added, `removeTemplate` emit added, `handleDelete` branched for templates, action panel `v-if` simplified
- `../frontend/src/components/workout/ExerciseCard.vue` — `removeTemplate` emit declared, `handleRemoveTemplate` function added, `@remove-template` wired on SetRow
